import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Optional
from typing import List

from fastapi import HTTPException, status
from sqlalchemy import select, and_, func, Integer, delete, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.api_schemas.poll import QuestionCreate, PollCreate, VoteRequest, AnswerRequest, PollSummary, \
    PollStatusUpdate, OptionResult, PollResultsResponse, AverageValue, QuestionOptionCreate
from src.db.models import Poll, Question, QuestionOption, Submission, Answer, AiRequest, AiChatMessage

logger = logging.getLogger(__name__)


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
                    "Возможно, транзакция в /generate была откатчена из-за таймаута. "
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
            Submission.respondent_token == respondent_token
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
    if poll.expires_at and poll.expires_at < completed_time:
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
    Возвращает список опросов пользователя с подсчитанным количеством завершённых голосов.
    Использует один запрос с LEFT JOIN + COUNT для избежания N+1 проблемы.
    """
    stmt = (
        select(
            Poll.id,
            Poll.title,
            Poll.status,
            Poll.poll_type,
            Poll.created_at,
            Poll.expires_at,
            func.count(Submission.id).filter(
                Submission.completed_at.isnot(None)
            ).label("total_votes")
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
            id=row.id,
            title=row.title,
            status=row.status,
            type=row.poll_type,
            created_at=row.created_at,
            expires_at=row.expires_at,
            total_votes=row.total_votes
        )
        for row in rows]


async def update_poll_status_service(
        db: AsyncSession,
        poll_id: int,
        user_id: int,
        status_in: PollStatusUpdate
) -> PollSummary:
    """
        Обновляет статус опроса. Проверяет права доступа и возвращает обновлённые данные.
        """
    # Находим опрос и проверяем, что он принадлежит текущему пользователю
    stmt = select(Poll).where(Poll.id == poll_id, Poll.created_by_user_id == user_id)
    result = await db.execute(stmt)
    poll = result.scalar_one_or_none()

    if not poll:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Опрос не найден или у вас нет прав на его изменение"
        )

    # if poll.status == "closed" and status_in.status != "closed":
    #     raise HTTPException(400, detail="Нельзя изменить статус закрытого опроса")
    if poll.status == "active" and status_in.status == "draft":
        raise HTTPException(400, detail="Нельзя вернуть активный опрос в черновик")

    # Обновляем статус
    poll.status = status_in.status
    await db.commit()
    await db.refresh(poll)

    # Считаем актуальное количество голосов (один быстрый запрос)
    count_stmt = select(func.count(Submission.id)).where(
        Submission.poll_id == poll_id, Submission.completed_at.isnot(None)
    )
    count_result = await db.execute(count_stmt)
    total_votes = count_result.scalar() or 0

    return PollSummary(
        id=poll.id,
        title=poll.title,
        status=poll.status,
        type=poll.poll_type,
        created_at=poll.created_at,
        expires_at=poll.expires_at,
        total_votes=total_votes
    )


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
    result = await db.execute(stmt)
    poll = result.scalar_one_or_none()

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
            exclude_unset=True  # Меняет только явно переданные поля
        )
        for field, value in update_data.items():
            if hasattr(poll, field):
                setattr(poll, field, value)

        # 3. Автозаполнение даты публикации
        if poll.status == "active" and poll.published_at is None:
            poll.published_at = datetime.now(timezone.utc)

        # 4. Удаление старого дерева вопросов
        await db.execute(
            delete(QuestionOption).where(
                QuestionOption.question_id.in_(
                    select(Question.id).where(Question.poll_id == poll_id)
                )
            )
        )
        await db.execute(delete(Question).where(Question.poll_id == poll_id))
        await db.flush()

        # 5. Добавление новых вопросов
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

    # 6. Формирование ответа
    count_stmt = select(func.count(Submission.id)).where(
        Submission.poll_id == poll_id,
        Submission.completed_at.isnot(None)
    )
    total_votes = (await db.execute(count_stmt)).scalar() or 0

    return PollSummary(
        id=poll.id,
        title=poll.title,
        status=poll.status,
        type=poll.poll_type,
        created_at=poll.created_at,
        expires_at=poll.expires_at,
        total_votes=total_votes)


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
    options_list = [option_text for question_id, option_text, option_pos, count in votes_data]
    votes_q_data = {q.id: q.q_count for q in votes_q_results.all()}
    results_list = []
    for question_id, option_text, option_pos, count in votes_data:  # Сохраняем результаты по вариантам
        question_pos, question_text, _ = questions_map[question_id]
        q_count = votes_q_data[question_id]
        option_result = OptionResult(
            question=question_text,
            question_position=question_pos,
            option_position=option_pos,
            option=option_text,
            votes=count,
            percentage=round(count / q_count * 100, 2) if q_count > 0 else 0.0
        )
        results_list.append(option_result)
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
                Question.type == 'scale'
            )
            .group_by(Question.id)
        )
        rating_results = await db.execute(rating_avg_query)
        for q_id, avg_val in rating_results:
            if avg_val is not None:
                q_pos, q_text, _ = questions_map[q_id]
                avg_res_list.append(AverageValue(
                    question=q_text,
                    question_position=q_pos,
                    avg_value=round(float(avg_val), 2),
                ))
    results_response = PollResultsResponse(
        id=poll.id,
        title=poll.title,
        options=options_list,
        description=poll.description,
        created_at=poll.created_at,
        total_votes=total_votes,
        votes=results_list,
        avg_values=avg_res_list,
        response_rate=response_rate_val,
        avg_completion_time=avg_completion_time_seconds
    )
    return results_response
