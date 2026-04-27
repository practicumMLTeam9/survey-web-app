from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, BOOLEAN, Enum as SQLEnum, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import datetime
from sqlalchemy.orm import DeclarativeBase
from enum import Enum as PyEnum


class Base(DeclarativeBase): pass


class PollStatus(PyEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"

    @classmethod
    def choices(cls):
        return [status.value for status in cls]


class Poll(Base):
    __tablename__ = 'polls'

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[PollStatus] = mapped_column(
        SQLEnum(PollStatus, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=PollStatus.DRAFT
        , name="poll_status_enum"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now())
    created_by_user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    # ORM
    questions: Mapped[list["Question"]] = relationship(back_populates="poll", cascade="all, delete-orphan")
    submissions: Mapped[list["Submission"]] = relationship(back_populates="poll", cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = 'questions'

    id: Mapped[int] = mapped_column(primary_key=True)
    poll_id:Mapped[int] = mapped_column(ForeignKey('polls.id'), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. "single", "multiple", "text"
    is_required: Mapped[bool]= mapped_column(BOOLEAN, nullable=False, default=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    # ORM
    poll: Mapped["Poll"] = relationship(back_populates="questions")
    options: Mapped[list["QuestionOption"]] = relationship(back_populates="question", cascade="all, delete-orphan")


class QuestionOption(Base):
    __tablename__ = 'question_options'

    id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey('questions.id'), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # ORM
    question: Mapped["Question"] = relationship(back_populates="options")


class Submission(Base):
    __tablename__ = 'submissions'

    d: Mapped[int] = mapped_column(primary_key=True)
    poll_id: Mapped[int] = mapped_column(ForeignKey('polls.id'), nullable=False)
    respondent_token: Mapped[str] = mapped_column(String(64), nullable=False)  # UUID/хеш
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True
    )
    # ORM
    poll: Mapped["Poll"] = relationship(back_populates="submissions")
    answers: Mapped[list["Answer"]] = relationship(back_populates="submission", cascade="all, delete-orphan")


class Answer(Base):
    __tablename__ = 'answers'

    id: Mapped[int] = mapped_column(primary_key=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey('submissions.id'), nullable=False)
    question_id: Mapped[int] = mapped_column(ForeignKey('questions.id'), nullable=False)
    option_id: Mapped[int | None] = mapped_column(ForeignKey('question_options.id'))  # NULL для текстовых вопросов
    text_value: Mapped[str | None] = mapped_column(Text)  # Для текстовых ответов
    # ORM
    submission: Mapped["Submission"] = relationship(back_populates="answers")
    question: Mapped["Question"] = relationship()
    option: Mapped["QuestionOption | None"] = relationship()
