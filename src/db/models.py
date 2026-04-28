from sqlalchemy import text, Integer, String, DateTime, Text, ForeignKey, func, UniqueConstraint, CheckConstraint, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import datetime
from sqlalchemy.orm import DeclarativeBase
from enum import Enum as PyEnum


class Base(DeclarativeBase): pass


class PollStatus(PyEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    CLOSED = "closed"

    @classmethod
    def choices(cls):
        return [status.value for status in cls]


class QuestionType(PyEnum):
    SINGLE = 'single_choice'
    MULTIPLE = 'multiple_choice'
    TEXT = 'text'
    SCALE = 'scale'

    @classmethod
    def types(cls):
        return [type.value for type in cls]


class Poll(Base):
    __tablename__ = 'polls'
    __table_args__ = (
        CheckConstraint("status IN ('draft', 'active', 'closed')", name="check_status"),
        {'comment': 'Опросы, создаваемые пользователями'})

    id: Mapped[int] = mapped_column(primary_key=True, comment='Уникальный идентификатор опроса')
    title: Mapped[str] = mapped_column(Text, nullable=False, comment='Название опроса')
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment='Описание опроса')
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=text("'draft'"),
        comment='Статус опроса (draft, active, closed)'
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment='Дата создания'
    )
    created_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=True, comment='ID пользователя, создавшего опрос')
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        server_default=func.now(),
        onupdate=func.now(),  # ???
        comment='Дата последнего обновления'
    )
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment='Дата публикации',
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment='Дата окончания опроса')
    is_anonymous: Mapped[bool] = mapped_column(Boolean, server_default=text("true"), nullable=True,
                                               comment='Признак анонимного опроса')
    one_response_only: Mapped[bool] = mapped_column(Boolean, server_default=text("true"), nullable=True,
                                                    comment='Разрешен только один ответ от пользователя')
    # ORM
    questions: Mapped[list["Question"]] = relationship(back_populates="poll", cascade="all, delete-orphan")
    submissions: Mapped[list["Submission"]] = relationship(back_populates="poll", cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = 'questions'
    __table_args__ = (
        CheckConstraint("type IN ('single_choice', 'multiple_choice', 'text', 'scale')", name="check_question_type"),
        {'comment': 'Вопросы внутри опроса'})

    id: Mapped[int] = mapped_column(primary_key=True, comment='Уникальный идентификатор вопроса')
    poll_id: Mapped[int] = mapped_column(
        ForeignKey('polls.id', ondelete="CASCADE"),
        nullable=False, index=True, comment='ID опроса'
    )
    text: Mapped[str] = mapped_column(Text, nullable=False, comment='Текст вопроса')
    type: Mapped[str] = mapped_column(
        String(20), nullable=False, comment='Тип вопроса (single_choice, multiple_choice, text, scale)')
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"),
                                              comment='Обязательный ли вопрос')
    position: Mapped[int] = mapped_column(Integer, nullable=False, comment='Порядок отображения вопроса')
    # ORM
    poll: Mapped["Poll"] = relationship(back_populates="questions")
    options: Mapped[list["QuestionOption"]] = relationship(back_populates="question", cascade="all, delete-orphan")


class QuestionOption(Base):
    __tablename__ = 'question_options'
    __table_args__ = {"comment": 'Варианты ответов для вопросов'}

    id: Mapped[int] = mapped_column(primary_key=True, comment='ID варианта ответа')
    question_id: Mapped[int] = mapped_column(
        ForeignKey('questions.id', ondelete="CASCADE"),
        nullable=False, comment='ID вопроса', index=True
    )
    text: Mapped[str] = mapped_column(Text, nullable=False, comment='Текст варианта')
    position: Mapped[int] = mapped_column(Integer, nullable=False, comment='Порядок отображения варианта')
    # ORM
    question: Mapped["Question"] = relationship(back_populates="options")


class Submission(Base):
    __tablename__ = 'submissions'
    __table_args__ = (
        UniqueConstraint('poll_id', 'respondent_token', name='uniq_submission'),
        {"comment": 'Факт прохождения опроса пользователем'}
    )

    id: Mapped[int] = mapped_column(primary_key=True, comment='ID прохождения')
    poll_id: Mapped[int] = mapped_column(
        ForeignKey('polls.id', ondelete="CASCADE"),
        nullable=False, index=True, comment='ID прохождения')
    respondent_token: Mapped[str] = mapped_column(String(64), nullable=True,
                                                  comment='Анонимный идентификатор пользователя')  # хеш
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment='Дата отправки ответов')
    # ORM
    poll: Mapped["Poll"] = relationship(back_populates="submissions")
    answers: Mapped[list["Answer"]] = relationship(back_populates="submission", cascade="all, delete-orphan")


class Answer(Base):
    __tablename__ = 'answers'
    __table_args__ = {"comment": "Ответы пользователей на вопросы"}

    id: Mapped[int] = mapped_column(primary_key=True, comment='ID прохождения опроса')
    submission_id: Mapped[int] = mapped_column(
        ForeignKey('submissions.id', ondelete='CASCADE'),
        nullable=False, index=True, comment='ID прохождения опроса')
    question_id: Mapped[int] = mapped_column(
        ForeignKey('questions.id', ondelete='CASCADE'),
        nullable=False, index=True, comment='ID вопроса')
    option_id: Mapped[int | None] = mapped_column(
        ForeignKey('question_options.id', ondelete='CASCADE'),
        nullable=True, index=True, comment='ID выбранного варианта')  # NULL для текстовых вопросов
    text_value: Mapped[str | None] = mapped_column(Text, nullable=True, comment='Текстовый ответ')
    # ORM
    submission: Mapped["Submission"] = relationship(back_populates="answers")
    question: Mapped["Question"] = relationship()
    option: Mapped["QuestionOption | None"] = relationship()


class User(Base):
    __tablename__ = 'users'
    __table_args__ = (
        UniqueConstraint('email', name='users_email_key'),
        {"comment": "Зарегистрированные пользователи системы"}
    )

    id: Mapped[int] = mapped_column(primary_key=True, comment="Уникальный идентификатор пользователя")
    email: Mapped[str] = mapped_column(Text, nullable=False, comment="Email пользователя для входа")
    password_hash: Mapped[str] = mapped_column(Text, nullable=False, comment="Хеш пароля")
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        server_default=func.now(),
        comment="Дата регистрации"
    )
    reset_token_hash: Mapped[str | None] = mapped_column(Text, nullable=True, comment="Хеш токена сброса пароля")
    reset_token_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Срок действия токена сброса пароля"
    )
    # ORM
    polls: Mapped[list["Poll"]] = relationship(back_populates="creator")


class AiChatMessage(Base):
    __tablename__ = 'ai_chat_messages'
    __table_args__ = {"comment": "История общения пользователя с AI по опросу"}

    id: Mapped[int] = mapped_column(primary_key=True, comment="ID сообщения")
    poll_id: Mapped[int] = mapped_column(
        ForeignKey('polls.id', ondelete="CASCADE"),
        nullable=False, index=True, comment="ID опроса"  # idx_ai_chat_poll_id покрыт через index=True
    )
    role: Mapped[str] = mapped_column(Text, nullable=False, comment="Роль (user или assistant)")
    message_text: Mapped[str] = mapped_column(Text, nullable=False, comment="Текст сообщения")
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, server_default=func.now(), comment="Дата сообщения"
    )
    # ORM
    poll: Mapped["Poll"] = relationship(back_populates="ai_chat_messages")


class AiSummary(Base):
    __tablename__ = 'ai_summaries'
    __table_args__ = {"comment": "AI-резюме по результатам опроса"}

    id: Mapped[int] = mapped_column(primary_key=True, comment="ID резюме")
    poll_id: Mapped[int] = mapped_column(
        ForeignKey('polls.id', ondelete="CASCADE"),
        nullable=False, index=True, comment="ID опроса"  # idx_ai_summary_poll_id покрыт через index=True
    )
    summary_text: Mapped[str] = mapped_column(Text, nullable=False, comment="Сгенерированный текст резюме")
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, server_default=func.now(), comment="Дата генерации")
    # ORM
    poll: Mapped["Poll"] = relationship(back_populates="ai_summaries")