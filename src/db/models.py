from sqlalchemy import text, Integer, DateTime, Text, ForeignKey, func, UniqueConstraint, CheckConstraint, \
    Boolean, false, true
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
        return [question_type.value for question_type in cls]


class Poll(Base):
    __tablename__ = 'polls'
    __table_args__ = (
        CheckConstraint("status IN ('draft', 'active', 'closed')", name="check_status"),
        {'comment': 'Опросы, создаваемые пользователями'})

    id: Mapped[int] = mapped_column(primary_key=True, comment='Уникальный идентификатор опроса')

    title: Mapped[str] = mapped_column(Text, nullable=False, comment='Название опроса')

    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment='Описание опроса')

    status: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'draft'"),
                                        index=True, comment='Статус опроса (draft, active, closed)')
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment='Дата создания')

    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
        index=True, comment='ID пользователя, создавшего опрос')

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        server_default=func.now(),
        comment='Дата последнего обновления')

    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment='Дата публикации')

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment='Дата окончания опроса')

    is_anonymous: Mapped[bool] = mapped_column(Boolean, server_default=true(), nullable=True,
                                               comment='Признак анонимного опроса')
    one_response_only: Mapped[bool] = mapped_column(Boolean, server_default=true(), nullable=True,
                                                    comment='Ограничение на один ответ от одного участника')
    poll_type: Mapped[str] = mapped_column(Text, nullable=True, server_default=text("'corporate'"),
                                           comment='Тип опроса, например corporate или client')
    language: Mapped[str] = mapped_column(Text, nullable=True, server_default=text("'ru'"),
                                          comment="Язык опроса")
    max_participants: Mapped[int] = mapped_column(Integer, nullable=True,
                                                  comment="Максимальное количество участников опроса")
    show_progress: Mapped[bool] = mapped_column(Boolean, nullable=True, server_default=true(),
                                                comment="Показывать ли участнику прогресс прохождения опроса")
    notify_on_response: Mapped[bool] = mapped_column(Boolean, nullable=True, server_default=false(),
                                                     comment="Отправлять ли уведомление при новом ответе")
    generated_by_ai: Mapped[bool] = mapped_column(Boolean, nullable=True, server_default=false(),
                                                  comment="Признак того, что опрос был сгенерирован с помощью AI")
    ai_generation_prompt: Mapped[str] = mapped_column(Text, nullable=True,
                                                      comment="Промпт, по которому AI генерировал опрос")
    target_participants: Mapped[int] = mapped_column(Integer, nullable=True,
                                                     comment="Планируемое или ожидаемое количество участников опроса")
    # ORM
    creator: Mapped["User | None"] = relationship("User", back_populates="polls")
    questions: Mapped[list["Question"]] = relationship(back_populates="poll",
                                                       cascade="all, delete-orphan",
                                                       passive_deletes=True)
    submissions: Mapped[list["Submission"]] = relationship(back_populates="poll",
                                                           cascade="all, delete-orphan",
                                                           passive_deletes=True)
    ai_summaries: Mapped[list["AiSummary"]] = relationship("AiSummary", back_populates="poll",
                                                            cascade="all, delete-orphan",
                                                            passive_deletes=True)
    ai_chat_messages: Mapped[list["AiChatMessage"]] = relationship("AiChatMessage", back_populates="poll",
                                                            cascade="all, delete-orphan",
                                                            passive_deletes=True)
    ai_requests: Mapped[list["AiRequest"]] = relationship("AiRequest", back_populates="poll",
                                                          cascade="all, delete-orphan",
                                                            passive_deletes=True)


class Question(Base):
    __tablename__ = 'questions'
    __table_args__ = (
        CheckConstraint("type IN ('single_choice', 'multiple_choice', 'text', 'scale')",
                        name="check_question_type"),
        {'comment': 'Вопросы внутри опроса'})

    id: Mapped[int] = mapped_column(primary_key=True, comment='Уникальный идентификатор вопроса')

    poll_id: Mapped[int] = mapped_column(ForeignKey('polls.id', ondelete="CASCADE"),
                                         nullable=False, index=True, comment='ID опроса, к которому относится вопрос')

    text: Mapped[str] = mapped_column(Text, nullable=False, comment='Текст вопроса')

    type: Mapped[str] = mapped_column(Text, nullable=False,
                                      comment='Тип вопроса (single_choice, multiple_choice, text, scale)')
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=false(),
                                              comment='Признак обязательного вопроса')
    position: Mapped[int] = mapped_column(Integer, nullable=False, comment='Порядок отображения вопроса в опросе')

    # ORM
    poll: Mapped["Poll"] = relationship("Poll", back_populates="questions")
    options: Mapped[list["QuestionOption"]] = relationship("QuestionOption", back_populates="question",
                                                           cascade="all, delete-orphan",
                                                           passive_deletes=True)
    answers: Mapped[list["Answer"]] = relationship("Answer", back_populates="question",
                                                   cascade="all, delete-orphan",
                                                   passive_deletes=True)


class QuestionOption(Base):
    __tablename__ = 'question_options'
    __table_args__ = {"comment": 'Варианты ответов для вопросов с выбором'}

    id: Mapped[int] = mapped_column(primary_key=True, comment='Уникальный идентификатор варианта ответа')

    question_id: Mapped[int] = mapped_column(
        ForeignKey('questions.id', ondelete="CASCADE"), nullable=False,
        index=True, comment='ID вопроса, к которому относится вариант')

    text: Mapped[str] = mapped_column(Text, nullable=False, comment='Текст варианта ответа')

    position: Mapped[int] = mapped_column(Integer, nullable=False, comment='Порядок отображения варианта ответа')

    # ORM
    question: Mapped["Question"] = relationship("Question", back_populates="options")
    answers: Mapped[list["Answer"]] = relationship("Answer", back_populates="option",
                                                   cascade="all, delete-orphan",
                                                   passive_deletes=True)


class Submission(Base):
    __tablename__ = 'submissions'
    __table_args__ = (
        UniqueConstraint('poll_id', 'respondent_token', name='uniq_submission'),
        {"comment": 'Факты прохождения опросов участниками'}
    )

    id: Mapped[int] = mapped_column(primary_key=True, comment='ID прохождения')

    poll_id: Mapped[int] = mapped_column(
        ForeignKey('polls.id', ondelete="CASCADE"),
        nullable=False, index=True, comment='ID опроса, который прошёл участник')  # Индекс

    respondent_token: Mapped[str] = mapped_column(Text, nullable=True,
                                                  comment='Анонимный идентификатор пользователя')  # хеш
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False,
                                                 comment='Дата создания прохождения')
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True,
                                                 comment="Дата и время начала прохождения опроса")
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True,
                                                   comment="Дата и время завершения прохождения опроса")
    # ORM
    poll: Mapped["Poll"] = relationship("Poll", back_populates="submissions")
    answers: Mapped[list["Answer"]] = relationship("Answer", back_populates="submission",
                                                   cascade="all, delete-orphan",
                                                   passive_deletes=True)


class Answer(Base):
    __tablename__ = 'answers'
    __table_args__ = {"comment": "Ответы участников на вопросы опроса"}

    id: Mapped[int] = mapped_column(primary_key=True, comment='Уникальный идентификатор ответа')

    submission_id: Mapped[int] = mapped_column(ForeignKey('submissions.id', ondelete='CASCADE'),
                                               nullable=False, index=True, comment='ID прохождения опроса')
    question_id: Mapped[int] = mapped_column(ForeignKey('questions.id', ondelete='CASCADE'),
                                             nullable=False, index=True, comment='ID вопроса, на который дан ответ')
    option_id: Mapped[int | None] = mapped_column(ForeignKey('question_options.id', ondelete='CASCADE'),
                                                  nullable=True, index=True, comment='ID выбранного варианта ответа')
    text_value: Mapped[str | None] = mapped_column(Text, nullable=True, comment='Текстовый ответ участника')
    # ORM
    submission: Mapped["Submission"] = relationship("Submission", back_populates="answers")
    question: Mapped["Question"] = relationship("Question", back_populates="answers")
    option: Mapped["QuestionOption | None"] = relationship("QuestionOption", back_populates="answers")


class User(Base):
    __tablename__ = 'users'
    __table_args__ = (
        UniqueConstraint('email', name='users_email_key'),
        {"comment": "Зарегистрированные пользователи системы"}
    )

    id: Mapped[int] = mapped_column(primary_key=True, comment="Уникальный идентификатор пользователя")

    email: Mapped[str] = mapped_column(Text, nullable=False, index=True,
                                       comment="Email пользователя для входа")  # Индекс
    password_hash: Mapped[str] = mapped_column(Text, nullable=False, comment="Хеш пароля пользователя")

    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        server_default=func.now(),
        comment="Дата создания аккаунта")

    reset_token_hash: Mapped[str | None] = mapped_column(Text, nullable=True, comment="Хеш токена для сброса пароля")

    reset_token_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Срок действия токена сброса пароля")

    first_name: Mapped[str] = mapped_column(Text, nullable=True, comment="Имя пользователя")

    last_name: Mapped[str] = mapped_column(Text, nullable=True, comment="Фамилия пользователя")

    company_name: Mapped[str] = mapped_column(Text, nullable=True, comment="Название компании пользователя")

    position: Mapped[str] = mapped_column(Text, nullable=True, comment="Должность пользователя")

    phone: Mapped[str] = mapped_column(Text, nullable=True, comment="Телефон пользователя")

    interface_language: Mapped[str] = mapped_column(Text, nullable=True, server_default=text("'ru'"),
                                                    comment="Язык интерфейса пользователя")
    role: Mapped[str] = mapped_column(Text, nullable=True, server_default=text("'user'"),
                                      comment="Роль пользователя в системе")
    avatar_url: Mapped[str] = mapped_column(Text, nullable=True, comment="Ссылка на аватар пользователя")

    # ORM
    polls: Mapped[list["Poll"]] = relationship("Poll", back_populates="creator",
                                               cascade="save-update, merge",
                                               lazy="selectin")                     # LAZY
    subscriptions: Mapped[list["Subscription"]] = relationship("Subscription", back_populates="user",
                                                               cascade="save-update, merge",
                                                               passive_deletes=True)
    ai_requests: Mapped[list["AiRequest"]] = relationship("AiRequest", back_populates="user",
                                                          cascade="save-update, merge",
                                                          passive_deletes=True)


class Subscription(Base):
    __tablename__ = 'subscriptions'
    __table_args__ = (
        CheckConstraint("plan IN ('free', 'pro', 'enterprise')", name="check_subscription_plan"),
        CheckConstraint("status IN ('active', 'expired', 'cancelled')", name="check_subscription_status"),
        {"comment": "Подписки пользователей и тарифные планы"}
    )

    id: Mapped[int] = mapped_column(primary_key=True, comment="Уникальный идентификатор подписки")

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ID пользователя, которому принадлежит подписка"
    )

    plan: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'free'"),
        comment="Тарифный план: free, pro, enterprise"
    )

    status: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'active'"),
        comment="Статус подписки: active, expired, cancelled"
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, server_default=func.now(),
        comment="Дата начала действия подписки"
    )

    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Дата окончания действия подписки"
    )
    # ORM
    user: Mapped["User"] = relationship("User", back_populates="subscriptions")


class AiChatMessage(Base):
    __tablename__ = 'ai_chat_messages'
    __table_args__ = {"comment": "История общения пользователя с AI по конкретному опросу"}

    id: Mapped[int] = mapped_column(primary_key=True, comment="Уникальный идентификатор сообщения")

    poll_id: Mapped[int] = mapped_column(
        ForeignKey('polls.id', ondelete="CASCADE"),
        nullable=False, index=True, comment="ID опроса, по которому ведётся AI-диалог")

    role: Mapped[str] = mapped_column(Text, nullable=False,
                                      comment="Роль автора сообщения: user или assistant")

    message_text: Mapped[str] = mapped_column(Text, nullable=False, comment="Текст сообщения в AI-чате")

    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, server_default=func.now(), comment="Дата создания сообщения")

    # ORM
    poll: Mapped["Poll"] = relationship(back_populates="ai_chat_messages")


class AiSummary(Base):
    __tablename__ = 'ai_summaries'
    __table_args__ = {"comment": "AI-резюме по результатам опроса"}

    id: Mapped[int] = mapped_column(primary_key=True, comment="Уникальный идентификатор AI-резюме")

    poll_id: Mapped[int] = mapped_column(
        ForeignKey('polls.id', ondelete="CASCADE"),
        nullable=False, index=True, comment="ID опроса, к которому относится AI-резюме")

    summary_text: Mapped[str] = mapped_column(Text, nullable=False, comment="Текст AI-резюме по результатам опроса")

    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, server_default=func.now(), comment="Дата генерации AI-резюме")
    # ORM
    poll: Mapped["Poll"] = relationship("Poll", back_populates="ai_summaries")


class AiRequest(Base):
    __tablename__ = 'ai_requests'
    __table_args__ = (
        CheckConstraint(
            "request_type IN ('generate_poll', 'summary', 'chat')",
            name="check_ai_request_type"
        ),
        {"comment": "Логи AI-запросов для учёта использования AI-функций"})

    id: Mapped[int] = mapped_column(primary_key=True, comment="Уникальный идентификатор AI-запроса")

    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True, index=True,
        comment="ID пользователя, который инициировал AI-запрос")

    poll_id: Mapped[int | None] = mapped_column(
        ForeignKey("polls.id", ondelete="CASCADE"),
        nullable=True, index=True,
        comment="ID опроса, связанного с AI-запросом")

    request_type: Mapped[str] = mapped_column(
        Text, nullable=False,
        comment="Тип AI-запроса: generate_poll, summary, chat")

    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, server_default=func.now(),
        index=True, comment="Дата создания AI-запроса")

    # ORM
    user: Mapped["User | None"] = relationship("User", back_populates="ai_requests")
    poll: Mapped["Poll | None"] = relationship("Poll", back_populates="ai_requests")
