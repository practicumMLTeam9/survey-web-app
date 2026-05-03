from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, and_
from fastapi import HTTPException, status
from typing import List, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from src.db.models import Poll, Question, QuestionOption, Submission, Answer
from src.api_schemas.poll import PollCreate, VoteRequest


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
    completed_time = datetime.now(timezone.utc)
    """Проверка существования и активности опроса"""
    query = select(Poll).where(
        and_(Poll.id == poll_id, Poll.status == 'active')
    )
    result_poll = await db.execute(query)
    poll = result_poll.scalar_one_or_none()
    if not poll:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Опрос не найден или не активен"
        )
    """Проверка существования вопроса в опросе"""
    for question in vote:
        query = select(Question).where(
            and_(
                Question.id == question.question_id,
                Question.poll_id == poll_id
            )
        )
        result_question = await db.execute(query)
        question = result_question.scalar_one_or_none()   
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Вопрос не найден в указанном опросе"
            )
    """Проверка существования варианта ответа"""
    for answer in vote:
        query = select(QuestionOption).where(
            and_(
                QuestionOption.id == answer.option_id,
                QuestionOption.question_id == answer.question_id
            )
        )
        result_answer = await db.execute(query)
        option = result_answer.scalar_one_or_none()
        if not option:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Вариант ответа не найден или не принадлежит указанному вопросу"
            )
    """Проверка, голосовал ли уже пользователь в этом опросе"""
    query = select(Submission).where(
        and_(
            Submission.poll_id == poll_id,
            Submission.respondent_token == respondent_token
        )
    )
    existing_submission = await db.execute(query)
    if existing_submission:
            # Пользователь уже голосовал - отклоняем голос
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Вы уже участвовали в этом опросе. Повторное голосование невозможно."
            )
    answers=[]
    submission = Submission(
            poll_id=poll_id,
            respondent_token=respondent_token,
            started_at=vote.started_time,
            completed_at=completed_time 
        )
    db.add(submission)
    await db.flush()  # Получаем submission.id
    # Создаем ответ пользователя
    for answer in vote:
        answer = Answer(
            submission_id=submission.id,
            question_id=answer.question_id,
            option_id=answer.option_id,
            text_value=answer.text_value
        )
        db.add(answer)
        answers.append(answer)
    try:
        await db.commit()   # сохраняем в БД
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при сохранении ответа: {str(e)}"     # str(e) для отлдаки
        )
    return answers