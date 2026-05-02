from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from typing import List, Any

from src.db.models import Poll, Question, QuestionOption
from src.api_schemas.poll import PollCreate


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


def create_poll_service(db: Session, poll_in: PollCreate, user_id: int) -> int:
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
    #    Поля, оставшиеся unset, НЕ попадут в SQL INSERT.
    #    PostgreSQL самостоятельно подставит значения из DEFAULT или запишет NULL.
    for field_name, value in poll_in.model_dump(exclude={"questions"}, exclude_none=True).items():
        if hasattr(poll, field_name):
            setattr(poll, field_name, value)

    db.add(poll)
    db.flush()  # Фиксируем poll.id для вложенных сущностей

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
        db.flush()  # Фиксируем question.id

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
        db.commit()
        db.refresh(poll)  # Синхронизируем объект с БД (на случай серверных триггеров/дефолтов)
        return poll.id
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Ошибка валидации данных опроса: нарушены ограничения БД"
        )
    except Exception:
        db.rollback()
        raise