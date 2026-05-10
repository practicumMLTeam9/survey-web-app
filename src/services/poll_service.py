from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, and_, func
from fastapi import HTTPException, status
from typing import List, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from src.db.models import Poll, Question, QuestionOption, Submission, Answer
from src.api_schemas.poll import PollCreate, VoteRequest, AnswerRequest, PollSummary
from collections import defaultdict


def _resolve_positions(items: List[Any]) -> List[int]:
    """
    Нормализует порядковые номера.
    Если позиции пропущены, дублируются или не идут подряд 1..N → генерирует заново.
    """
    positions = [item.position for item in items]
    n = len(items)
    valid_positions = list(range(1, n + 1))

    if any(p is None for p in positions):
        return valid_positions
    if len(set(positions)) != n:
        return valid_positions
    if sorted(positions) != valid_positions:
        return valid_positions

    return positions


async def create_poll_service(db: AsyncSession, poll_in: PollCreate, user_id: int) -> int:
    """
    Создаёт опрос с вопросами и вариантами ответов в одной транзакции.
    Возвращает ID созданного опроса.
    """
    # 1. Базовый опрос (только обязательные поля)
    poll = Poll(
        title=poll_in.title,
        description=poll_in.description,
        created_by_user_id=user_id,
        status="draft"
    )

    # 2. Опциональные поля: применяем ТОЛЬКО явно переданные клиентом.
    for field_name, value in poll_in.model_dump(exclude={"questions"}, exclude_none=True).items():
        if hasattr(poll, field_name):
            setattr(poll, field_name, value)

    db.add(poll)
    await db.flush()  # Фиксируем poll.id для вложенных сущностей

    # 3. Вопросы с нормализацией позиций
    q_positions = _resolve_positions(poll_in.questions)
    for q_in, q_pos in zip(poll_in.questions, q_positions):
        question = Question(
            poll_id=poll.id,
            text=q_in.text,
            type=q_in.type,
            position=q_pos,
            is_required=q_in.is_required
        )
        db.add(question)
        await db.flush()  # Фиксируем question.id

        # 4. Варианты ответов (только для choice-типов)
        if q_in.type in ("single_choice", "multiple_choice") and q_in.options:
            o_positions = _resolve_positions(q_in.options)
            for o_in, o_pos in zip(q_in.options, o_positions):
                option = QuestionOption(
                    question_id=question.id,
                    text=o_in.text,
                    position=o_pos
                )
                db.add(option)

    try:
        await db.commit()
        await db.refresh(poll)  # Синхронизируем объект с БД (на случай серверных триггеров/дефолтов)
        return poll.id
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Ошибка валидации данных опроса: нарушены ограничения БД"
        )
    except Exception:
        await db.rollback()
        raise


async def get_poll_with_details(db: AsyncSession, poll_id: int) -> Optional[Poll]:
    """
    Загружает опрос с вопросами и вариантами ответов.
    Вопросы и варианты автоматически сортируются по position на уровне БД.
    """
    stmt = (
        select(Poll)
        .where(Poll.id == poll_id)
        .options(
            selectinload(Poll.questions).selectinload(Question.options)
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def vote_poll_service(poll_id: int, 
                    vote: VoteRequest,
                    respondent_token: str, 
                    db: AsyncSession):
    completed_time = datetime.now(timezone.utc).replace(tzinfo=None)
    """Проверка существования и активности опроса"""
    poll_query = select(Poll).where(
        # and_(Poll.id == poll_id, Poll.status == 'active')
        Poll.id == poll_id
    )
    result_poll = await db.execute(poll_query)
    poll = result_poll.scalar_one_or_none()
    if not poll:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Опрос не найден или не активен"
        )
    """Проверка истечения времени для ответа"""
    if poll.expires_at and poll.expires_at < completed_time:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Время для прохождения опроса истекло"
        )
    """Проверка существования вопросов и корректности числа ответов на один вопрос"""
    answers_list = vote.answers
    checked_questions = set()
    answers_by_question = defaultdict(list)
    # Сначала группируем ответы по вопросам
    for answer in answers_list:
        answers_by_question[answer.question_id].append(answer)
    # Проверяем каждый вопрос
    for question_id, answers in answers_by_question.items():
        if question_id in checked_questions:
            continue    # если вопрос уже проверен - пропускаем
        question_query = select(Question).where(
            and_(
                Question.id == question_id,
                Question.poll_id == poll_id
            )
        )
        result_question = await db.execute(question_query)
        question = result_question.scalar_one_or_none()   
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Вопрос id:'{question_id}' не найден в опросе"
            )
        # Проверка для single_choice: не более одного ответа
        if question.type == "single_choice" and len(answers) > 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"На вопрос '{question.position}.{question.text}' (single_choice) передано {len(answers)} ответа. Допустим только один."
            )
        checked_questions.add(question_id)
    """Проверка на наличие обязательных ответов"""
    # Получаем список вопросов из опроса
    questions_query = select(Question).where(
            Question.poll_id == poll_id
    )
    result_questions = await db.execute(questions_query)
    questions = result_questions.scalars().all()
    for question in questions:
        if question.is_required and question.id not in answers_by_question:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Не получен ответ на обязательный вопрос: '{question.position}.{question.text}' "
            )
    """Проверка существования варианта ответа"""
    for answer in answers_list:
        answer_query = select(QuestionOption).where(
            and_(
                QuestionOption.id == answer.option_id,
                QuestionOption.question_id == answer.question_id
            )
        )
        result_answer = await db.execute(answer_query)
        option = result_answer.scalar_one_or_none()
        if not option:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Вариант ответа id:'{answer.option_id}' не найден или не принадлежит указанному вопросу"
            )
    """Проверка, голосовал ли уже пользователь в этом опросе"""
    if poll.one_response_only == True:
        submission_query = select(Submission).where(
            and_(
                Submission.poll_id == poll_id,
                Submission.respondent_token == respondent_token
            )
        )
        result_submission = await db.execute(submission_query)
        existing_submission = result_submission.scalar_one_or_none()
        if existing_submission:
                # Пользователь уже голосовал - отклоняем голос
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Вы уже участвовали в этом опросе. Повторное голосование невозможно."
                )
    submission = Submission(
            poll_id=poll_id,
            respondent_token=respondent_token,
            started_at=vote.started_time.replace(tzinfo=None),
            completed_at=completed_time 
        )
    db.add(submission)
    await db.flush()  # Получаем submission.id
    # Создаем ответ пользователя
    answers=[]
    for answer in answers_list:
        answer = Answer(
            submission_id=submission.id,
            question_id=answer.question_id,
            option_id=answer.option_id,
            text_value=answer.text_value
        )
        db.add(answer)
        added_answer = AnswerRequest.model_validate(answer)
        answers.append(added_answer)
    try:
        await db.commit()   # сохраняем в БД
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при сохранении ответа: {str(e)}"     # str(e) для отлдаки
        )
    return answers


async def get_list_polls(db: AsyncSession, user_id: int) -> list[PollSummary]:
    """
    Возвращает список опросов пользователя с подсчитанным количеством голосов.
    Использует один запрос с LEFT JOIN + COUNT для избежания N+1 проблемы.
    """
    stmt = (
        select(
            Poll.id,
            Poll.title,
            Poll.status,
            Poll.created_at,
            Poll.expires_at,
            func.count(Submission.id).label("total_votes")
        )
        .outerjoin(Submission, Poll.id == Submission.poll_id)
        .where(Poll.created_by_user_id == user_id)
        .group_by(Poll.id)  # Postgres автоматически включает остальные поля, если id — PK
        .order_by(Poll.created_at.desc())
    )

    result = await db.execute(stmt)
    rows = result.all()
    return [
        PollSummary(
            id=str(row.id),
            title=row.title,
            status=row.status,
            created_at=row.created_at,
            expires_at=row.expires_at,
            total_votes=row.total_votes
        )
        for row in rows
    ]


# def get_poll_results(poll_id: int, 
#                     user_id: int, 
#                     db: AsyncSession):
#     query = select(Poll).where(
#         and_(Poll.id == poll_id, Poll.creator == user_id)
#     )
#     result_poll = await db.execute(query)
#     poll = result_poll.scalar_one_or_none()
#     if poll is None:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Опрос не найден или не активен"
#         )
    