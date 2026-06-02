import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Optional
from typing import List

from fastapi import HTTPException, status
from sqlalchemy import cast
from sqlalchemy import select, and_, func, Integer, delete, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased
from sqlalchemy.orm import selectinload

from src.api_schemas.poll import QuestionCreate, PollCreate, VoteRequest, AnswerRequest, PollSummary, \
    PollStatusUpdate, OptionResult, PollResultsResponse, AverageValue, QuestionOptionCreate
from src.api_schemas.poll import QuestionResult
from src.db.models import Poll, Question, QuestionOption, Submission, Answer, AiRequest, AiChatMessage

logger = logging.getLogger(__name__)


async def _get_poll_stats(db: AsyncSession, poll_id: int) -> dict:
    """Получение статистики опроса."""
    votes_stmt = select(func.count(Submission.id)).where(
        Submission.poll_id == poll_id, Submission.completed_at.isnot(None)
    )
    questions_stmt = select(func.count(Question.id)).where(Question.poll_id == poll_id)

    votes_res = await db.execute(votes_stmt)
    questions_res = await db.execute(questions_stmt)
    return {
        "total_votes": votes_res.scalar() or 0,
        "questions_count": questions_res.scalar() or 0
    }


def _build_poll_summary(poll_data, stats: dict) -> PollSummary:
    """Унифицированный маппер ответа."""
    return PollSummary(
        id=poll_data.id,
        title=poll_data.title,
        status=poll_data.status,
        type=poll_data.poll_type,
        created_at=poll_data.created_at,
        expires_at=poll_data.expires_at,
        total_votes=stats["total_votes"],
        questions_count=stats["questions_count"]
    )


async def _sync_questions_tree(
        db: AsyncSession,
        poll: Poll,
        questions_in: List[QuestionCreate]
) -> None:
    """
    Синхронизирует дерево вопросов и вариантов ответов для опроса.
    Использует нормализацию позиций, автогенерацию шкалы и корректную обработку is_required.
    НЕ вызывает commit() — управление транзакцией остаётся у вызывающего метода.
    """
    types_with_options = ("single_choice", "multiple_choice", "scale")
    q_positions = _resolve_positions(questions_in)

    for q_in, q_pos in zip(questions_in, q_positions):
        question = Question(
            poll_id=poll.id,
            text=q_in.text,
            type=q_in.type,
            position=q_pos
        )
        # is_required: применяем только при явной передаче
        if q_in.is_required is not None:
            question.is_required = q_in.is_required

        db.add(question)
        await db.flush()  # Фиксируем question.id для привязки вариантов

        # Обработка вариантов ответов
        if q_in.type in types_with_options:
            options = list(q_in.options or [])

            # Автогенерация шкалы 1..5, если фронтенд не передал варианты
            if not options and q_in.type == "scale":
                options = [QuestionOptionCreate(text=str(i)) for i in range(1, 6)]

            if options:
                o_positions = _resolve_positions(options)
                for o_in, o_pos in zip(options, o_positions):
                    db.add(QuestionOption(
                        question_id=question.id,
                        text=o_in.text,
                        position=o_pos
                    ))


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
    #  Базовый опрос (только обязательные поля)
    poll = Poll(
        title=poll_in.title,
        description=poll_in.description,
        created_by_user_id=user_id)

    # Опциональные поля: применяем ТОЛЬКО явно переданные клиентом.
    for field_name, value in poll_in.model_dump(exclude={"questions"}, exclude_none=True).items():
        if hasattr(poll, field_name):
            setattr(poll, field_name, value)

    # Автозаполнение даты публикации, если клиент сразу ставит active
    if poll.status == "active" and poll.published_at is None:
        poll.published_at = datetime.now(timezone.utc)

    db.add(poll)
    await db.flush()  # Фиксируем poll.id для вложенных сущностей

    # Делегируем построение дерева общей функции
    await _sync_questions_tree(db, poll, poll_in.questions)

    try:
        # Логирование AI (если опрос создан из черновика)
        session_token = getattr(poll_in, "ai_request_session_token", None)

        if session_token:
            # Приводим к bool, так как в модели Mapped[bool | None], но фронтенд шлёт true/false
            was_edited = bool(getattr(poll_in, "user_edited_draft", False))

            update_stmt = (
                update(AiRequest)
                .where(AiRequest.session_token == session_token)
                .values(
                    poll_id=poll.id,
                    user_edited_draft=was_edited
                )
            )
            result = await db.execute(update_stmt)

            if result.rowcount == 0:
                logger.warning(
                    f"⚠️ AiRequest с session_token='{session_token[:8]}...' не найден. "
                    "Возможно, транзакция в /generate была откачена из-за таймаута. "
                    "Чат будет сохранён без привязки к бенчмарку."
                )
            # Сохраняем историю чата (ВЫПОЛНЯЕТСЯ ВСЕГДА, даже если UPDATE не сработал)
            chat_messages = [
                AiChatMessage(
                    poll_id=poll.id,
                    role="user",
                    message_text=poll_in.ai_generation_prompt or "Генерация опроса через AI"),
                AiChatMessage(
                    poll_id=poll.id,
                    role="assistant",
                    message_text=poll_in.model_dump_json(exclude={"ai_request_session_token", "ai_generation_prompt"}))
            ]
            db.add_all(chat_messages)
            logger.info(f"✅ Чат сохранён для poll_id={poll.id}")
            # Не делаем отдельный commit() — всё зафиксируется одним общим commit() ниже

        await db.commit()
        await db.refresh(poll)

        logger.info(
            f"✅ Poll created: id={poll.id}, user={user_id}, "
            f"ai_linked={bool(getattr(poll_in, 'ai_request_session_token', None))}, "
            f"num_questions={len(poll_in.questions)}"
        )
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


async def start_vote_service(poll_id: int,
                             respondent_token: str,
                             db: AsyncSession):
    started_time = datetime.now(timezone.utc)
    """Проверка существования и активности опроса"""
    poll_query = select(Poll).where(
        and_(Poll.id == poll_id, Poll.status == 'active')
    )
    result_poll = await db.execute(poll_query)
    poll = result_poll.scalar_one_or_none()
    if not poll:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Опрос не найден или не активен/достигнут лимит участников"
        )
    """Проверка, начал ли уже пользователь прохождение опроса"""
    existing_submission_query = select(Submission).where(
        and_(
            Submission.poll_id == poll_id,
            Submission.respondent_token == respondent_token,
        )
    )
    result_sub = await db.execute(existing_submission_query)
    existing_submission = result_sub.scalar_one_or_none()
    if existing_submission:
        # Если запись уже есть, просто возвращаем статус
        return {"status": "already_started"}
    # Создание новой записи о начале
    new_submission = Submission(
        poll_id=poll_id,
        respondent_token=respondent_token,
        started_at=started_time,
        completed_at=None  # Явно указываем, что опрос не завершен
    )
    db.add(new_submission)
    try:
        await db.commit()
        await db.refresh(new_submission)
        return {"started_at": new_submission.started_at}
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при начале прохождения опроса: {str(e)}"
        )


async def vote_poll_service(poll_id: int,
                            vote: VoteRequest,
                            respondent_token: str,
                            db: AsyncSession):
    completed_time = datetime.now(timezone.utc)
    """Проверка существования и активности опроса"""
    poll_query = select(Poll).where(
        and_(Poll.id == poll_id, Poll.status == 'active')
    ).with_for_update()
    result_poll = await db.execute(poll_query)
    poll = result_poll.scalar_one_or_none()
    if not poll:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Опрос не найден или не активен/достигнут лимит участников"
        )
    """Проверка истечения времени для ответа"""
    if poll.expires_at and poll.expires_at < completed_time.replace(tzinfo=None):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Время для прохождения опроса истекло"
        )
    """Проверка, голосовал ли уже пользователь в этом опросе
    Логика:
    1. Если completed_at IS NULL -> Разрешаем (пользователь начал, но не финишировал).
    2. Если completed_at IS NOT NULL -> Запрещаем (уже проголосовал).
    """
    if poll.one_response_only:
        submission_query = select(Submission).where(
            and_(
                Submission.poll_id == poll_id,
                Submission.respondent_token == respondent_token,
                Submission.completed_at.isnot(None)
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
    sub_query = select(Submission).where(
        and_(
            Submission.poll_id == poll_id,
            Submission.respondent_token == respondent_token,
            Submission.completed_at.is_(None)  # Ищем только незавершенные
        )
    ).order_by(Submission.started_at.desc())  # Берем самую свежую попытку
    result_sub = await db.execute(sub_query)
    sub = result_sub.scalar_one_or_none()
    if sub is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Прохождение опроса не начато"
        )
    sub.completed_at = completed_time
    await db.flush()
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
            continue  # если вопрос уже проверен - пропускаем
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
        if question.type in ("single_choice", "scale") and len(answers) > 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"На вопрос '{question.position}.{question.text}' (single_choice/scale) передано {len(answers)} ответа. Допустим только один."
            )
        # Проверка для multiple_choice: не более одного голоса за один из вариантов ответа
        if question.type == "multiple_choice":
            # Собираем все option_id из ответов на этот вопрос
            option_ids = [answer.option_id for answer in answers]
            # Проверяем на дубликаты ответов
            if len(option_ids) != len(set(option_ids)):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"На вопрос '{question.position}.{question.text}' (multiple_choice) обнаружены дубликаты вариантов ответов. Каждый вариант можно выбрать только один раз."
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
        if answer.option_id is not None:
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
    # Создаем ответ пользователя
    answers = []
    for answer in answers_list:
        answer = Answer(
            submission_id=sub.id,
            question_id=answer.question_id,
            option_id=answer.option_id,
            text_value=answer.text_value
        )
        db.add(answer)
        added_answer = AnswerRequest.model_validate(answer)
        answers.append(added_answer)
    """Проверка на соответствие максимальному числу участников"""
    if poll.max_participants is not None:
        count_res = await db.execute(
            select(func.count(Submission.id)).where(Submission.poll_id == poll_id, Submission.completed_at.isnot(None))
        )
        current_count = count_res.scalar() or 0
        if current_count >= poll.max_participants:
            poll.status = "closed"  # закрываем опрос, чтобы не превысить лимит участников
    try:
        await db.commit()  # сохраняем в БД
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при сохранении ответа: {str(e)}"  # str(e) для отлдаки
        )
    return answers


async def get_list_polls(db: AsyncSession, user_id: int) -> list[PollSummary]:
    """
    Возвращает список опросов пользователя с подсчитанным количеством завершённых голосов
    и количеством вопросов в опроснике.
    """
    votes_subq = select(func.count(Submission.id)).where(
        Submission.poll_id == Poll.id, Submission.completed_at.isnot(None)
    ).scalar_subquery()

    questions_subq = select(func.count(Question.id)).where(
        Question.poll_id == Poll.id
    ).scalar_subquery()

    stmt = (
        select(
            Poll,
            votes_subq.label("total_votes"),
            questions_subq.label("questions_count")
        )
        .where(Poll.created_by_user_id == user_id)
        .order_by(Poll.created_at.desc())
    )

    result = await db.execute(stmt)
    rows = result.all()
    return [
        _build_poll_summary(row.Poll, {
            "total_votes": row.total_votes or 0,
            "questions_count": row.questions_count or 0
        })
        for row in rows]


async def update_poll_status_service(
        db: AsyncSession,
        poll_id: int,
        user_id: int,
        status_in: PollStatusUpdate
) -> PollSummary:
    """Обновляет статус опроса и возвращает актуальную сводку."""

    stmt = select(Poll).where(Poll.id == poll_id, Poll.created_by_user_id == user_id)
    poll = (await db.execute(stmt)).scalar_one_or_none()

    if not poll:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Опрос не найден или у вас нет прав на его изменение")

    if poll.status == "active" and status_in.status == "draft":
        raise HTTPException(400, detail="Нельзя вернуть активный опрос в черновик")

    poll.status = status_in.status
    await db.commit()
    await db.refresh(poll)

    stats = await _get_poll_stats(db, poll.id)
    return _build_poll_summary(poll, stats)


async def update_poll_service(
        db: AsyncSession,
        poll_id: int,
        user_id: int,
        poll_update: PollCreate
) -> PollSummary:
    """
    Полное обновление черновика опроса.
    """
    # 1. Проверка прав
    stmt = select(Poll).where(Poll.id == poll_id, Poll.created_by_user_id == user_id)
    poll = (await db.execute(stmt)).scalar_one_or_none()

    if not poll:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Опрос не найден или у вас нет прав на его изменение")
    if poll.status != "draft":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Редактировать можно только опросы в статусе draft")

    try:
        # 2.ОБНОВЛЕНИЕ ПОЛЕЙ
        update_data = poll_update.model_dump(
            exclude={"questions"},
            exclude_unset=True)  # Меняет только явно переданные поля
        for field, value in update_data.items():
            if hasattr(poll, field):
                setattr(poll, field, value)

        # Автозаполнение даты публикации
        if poll.status == "active" and poll.published_at is None:
            poll.published_at = datetime.now(timezone.utc)

        # Удаление старого дерева вопросов
        await db.execute(
            delete(QuestionOption).where(
                QuestionOption.question_id.in_(
                    select(Question.id).where(Question.poll_id == poll_id))
            )
        )
        await db.execute(delete(Question).where(Question.poll_id == poll_id))
        await db.flush()

        # Добавление новых вопросов
        await _sync_questions_tree(db, poll, poll_update.questions)
        await db.commit()
        await db.refresh(poll)

    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="Ошибка валидации данных опроса: нарушены ограничения БД")
    except Exception:
        await db.rollback()
        raise

    stats = await _get_poll_stats(db, poll.id)
    return _build_poll_summary(poll, stats)

async def get_poll_results(poll_id: int,
                           user_id: int,
                           db: AsyncSession):
    """Проверка существования опроса"""
    poll_query = select(Poll).where(
        and_(Poll.id == poll_id, Poll.created_by_user_id == user_id)
    )
    result_poll = await db.execute(poll_query)
    poll = result_poll.scalar_one_or_none()
    if poll is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Опрос не найден или не активен"
        )
    """Общий подсчёт голосов"""
    total_votes_query = select(func.count(Submission.id)).where(
        Submission.poll_id == poll_id, Submission.completed_at.isnot(None)
    )
    total_votes = (await db.execute(total_votes_query)).scalar_one_or_none()
    if total_votes is None:
        total_votes = 0
    """Подсчёт голосов по вариантам ответа"""
    votes_opt_query = (
        select(QuestionOption.question_id, QuestionOption.text, QuestionOption.position, func.count(Answer.id))
        .outerjoin(Answer, QuestionOption.id == Answer.option_id)
        .join(Question, QuestionOption.question_id == Question.id)
        .where(Question.poll_id == poll_id)
        .group_by(QuestionOption.id, QuestionOption.question_id, QuestionOption.text, QuestionOption.position)
    )
    votes_opt_results = await db.execute(votes_opt_query)  # число ответов по вариантам
    votes_q_query = (
        select(Question.id, func.count(func.distinct(Submission.id)).label("q_count"))
        .outerjoin(Answer, Question.id == Answer.question_id)
        .join(Submission, Answer.submission_id == Submission.id)
        .where(Question.poll_id == poll_id)
        .group_by(Question.id)
    )
    votes_q_results = await db.execute(votes_q_query)  # число ответов по вопросу
    """Подсчёт среднего времени прохождения опроса"""
    avg_time_query = select(
        func.avg(Submission.completed_at - Submission.started_at)
    ).where(
        and_(
            Submission.poll_id == poll_id,
            Submission.started_at.isnot(None),
            Submission.completed_at.isnot(None)
        )
    )
    avg_time_result = await db.execute(avg_time_query)
    avg_completion_time = avg_time_result.scalar_one_or_none()
    avg_completion_time_seconds = (
        avg_completion_time.total_seconds() if avg_completion_time else 0.0
    )
    """Подсчёт отклика на опрос"""
    total_submissions_query = select(func.count(Submission.id)).where(
        Submission.poll_id == poll_id
    )
    total_submissions = (await db.execute(total_submissions_query)).scalar_one_or_none() or 0
    response_rate_val = round(total_votes / total_submissions * 100, 2) if total_submissions > 0 else 0.0
    """Информация о вопросах для вывода"""
    questions_query = select(Question.id, Question.position, Question.text, Question.type).where(
        Question.poll_id == poll_id)
    questions_result = await db.execute(questions_query)
    questions_map = {q.id: (q.position, q.text, q.type) for q in questions_result.all()}
    """Сохранение числа ответов по вариантам"""
    votes_data = [(question_id, option_text, option_pos, count) for question_id, option_text, option_pos, count in
                  votes_opt_results.all()]
    votes_q_data = {q.id: q.q_count for q in votes_q_results.all()}
    votes_list = []
    for question_id in questions_map:
        results_list = []
        text_answers = []
        question_pos, question_text, question_type = questions_map[question_id]
        if question_type != "text":
            for q_id, option_text, option_pos, count in votes_data:  # Сохраняем результаты по вариантам
                q_count = votes_q_data[question_id]
                if q_id == question_id:
                    option_result = OptionResult(
                        option_position=option_pos,
                        option=option_text,
                        votes=count,
                        percentage=round(count / q_count * 100, 2) if q_count > 0 else 0.0
                    )
                    results_list.append(option_result)
            # Сортируем по позиции
            results_list.sort(key=lambda x: x.option_position)
        else:
            answers_query = (
                select(Answer.text_value)
                .join(Question, Answer.question_id == Question.id)
                .where(
                    Question.poll_id == poll_id,
                    Question.type == 'text',
                    Answer.text_value.isnot(None),
                    Answer.text_value != '',  # ← исключаем пустые строки
                    Answer.text_value != 'string'  # ← исключаем "string"
                )
            )
            # Выполнение и сохранение в list
            result = await db.execute(answers_query)
            text_answers = result.scalars().all()
        question_result = QuestionResult(
            question_id=question_id,
            question_text=question_text,
            question_position=question_pos,
            question_type=question_type,
            question_votes=results_list,
            text_answers=text_answers if text_answers else []
        )
        votes_list.append(question_result)
    """Подсчёт среднего значения для опросов с типом scale"""
    avg_res_list = []
    if any(q[2] == 'scale' for q in questions_map.values()):
        rating_avg_query = (
            select(
                Question.id.label('question_id'),
                func.avg(QuestionOption.text.cast(Integer)).label('avg_rating')
            )
            .join(QuestionOption, Question.id == QuestionOption.question_id)
            .join(Answer, QuestionOption.id == Answer.option_id)
            .where(
                Question.poll_id == poll_id,
                Question.type == 'scale',
                QuestionOption.text.regexp_match(r'^-?\d+$')
            )
            .group_by(Question.id)
        )
        rating_results = await db.execute(rating_avg_query)
        for q_id, avg_val in rating_results:
            if avg_val is not None:
                q_pos, q_text, _ = questions_map[q_id]
                avg_res_list.append(AverageValue(
                    question_id=q_id,
                    question_text=q_text,
                    question_position=q_pos,
                    avg_value=round(float(avg_val), 2),
                ))
    results_response = PollResultsResponse(
        id=poll.id,
        title=poll.title,
        description=poll.description,
        poll_type=poll.poll_type,
        language=poll.language,
        created_at=poll.created_at,
        total_votes=total_votes,
        votes=votes_list,
        avg_values=avg_res_list,
        response_rate=response_rate_val,
        avg_completion_time=avg_completion_time_seconds
    )
    return results_response


async def get_text_answers(
        poll_id: int,
        user_id: int,
        db: AsyncSession
):
    """Проверка существования опроса"""
    poll_query = select(Poll).where(
        and_(Poll.id == poll_id, Poll.created_by_user_id == user_id)
    )
    result_poll = await db.execute(poll_query)
    poll = result_poll.scalar_one_or_none()
    if poll is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Опрос не найден или не активен"
        )
    all_answers = []

    # 1. Текстовые ответы — берём как есть
    text_query = (
        select(Answer.text_value)
        .join(Question, Answer.question_id == Question.id)
        .where(
            Question.poll_id == poll_id,
            Question.type == 'text',
            Answer.text_value.isnot(None),
            Answer.text_value != '',
            Answer.text_value != 'string'
        )
    )
    result = await db.execute(text_query)
    all_answers.extend(result.scalars().all())

    # 2. Ответы с выбором (single_choice, multiple_choice) — форматируем как текст
    choice_query = (
        select(Question.text, QuestionOption.text)
        .join(Answer, Answer.option_id == QuestionOption.id)
        .join(Question, Answer.question_id == Question.id)
        .where(
            Question.poll_id == poll_id,
            Question.type.in_(['single_choice', 'multiple_choice']),
            Answer.option_id.isnot(None)
        )
    )
    result = await db.execute(choice_query)
    for q_text, opt_text in result.all():
        all_answers.append(f"{q_text}: {opt_text}")

    # 3. Шкальные ответы — форматируем как текст
    scale_query = (
        select(Question.text, QuestionOption.text)
        .join(Answer, Answer.option_id == QuestionOption.id)
        .join(Question, Answer.question_id == Question.id)
        .where(
            Question.poll_id == poll_id,
            Question.type == 'scale',
            Answer.option_id.isnot(None)
        )
    )
    result = await db.execute(scale_query)
    for q_text, opt_text in result.all():
        all_answers.append(f"{q_text}: оценка {opt_text}")

    return all_answers, poll.title, poll.description, poll.poll_type, poll.language


async def get_aggregate_val(
        poll_id: int,
        user_id: int,
        db: AsyncSession,
        categorical_question_id: int, scale_question_id: int
):
    """Проверка существования опроса"""
    poll_query = select(Poll).where(
        and_(Poll.id == poll_id, Poll.created_by_user_id == user_id)
    )
    result_poll = await db.execute(poll_query)
    poll = result_poll.scalar_one_or_none()
    if poll is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Опрос не найден или не активен"
        )
    # Создаём алиасы для одной и той же таблицы QuestionOption
    category_option = aliased(QuestionOption)  # для ответа на категориальный вопрос
    scale_option = aliased(QuestionOption)  # для ответа на шкальный вопрос
    scale_answer = aliased(Answer)

    aggregation_query = (
        select(
            # Берём ТЕКСТ варианта из категориального ответа
            category_option.text.label('category'),
            # Среднее число из шкального ответа
            func.avg(cast(scale_option.text, Integer)).label('avg_scale')
        )
        .select_from(Submission)
        # Джойним ответы (категориальные)
        .join(Answer, Answer.submission_id == Submission.id)
        .join(category_option, category_option.id == Answer.option_id)
        .join(Question, Question.id == category_option.question_id)
        .where(Question.id == categorical_question_id)  # ID вопроса "Отдел"

        # Джойним ответы на шкальный вопрос (через алиас)
        .join(
            scale_answer,
            and_(
                scale_answer.submission_id == Submission.id,
                scale_answer.question_id == scale_question_id
            )
        )
        .join(scale_option, scale_option.id == scale_answer.option_id)
        .where(scale_option.text.regexp_match(r'^-?\d+$'))

        .group_by(category_option.text)
    )
    result = await db.execute(aggregation_query)
    aggregation_data = [
        {"category": row.category, "avg_scale": float(row.avg_scale)}
        for row in result
    ]
    return aggregation_data
