from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from src.db.models import Poll, Question, QuestionOption
from src.schemas.poll import PollCreate, QuestionCreate, QuestionOptionCreate

def create_poll_service(db: Session, poll_in: PollCreate, user_id: int) -> int:
    """
    Создаёт опрос с вопросами и вариантами ответов в одной транзакции.
    Возвращает ID созданного опроса.
    """