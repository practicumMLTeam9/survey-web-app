from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from datetime import datetime, timezone
from typing import List, Optional, Literal


# ─── Вспомогательные схемы ───
class QuestionOptionCreate(BaseModel):
    text: str = Field(..., min_length=1, max_length=500,
                      description="Текст варианта ответа")  # позиция вопроса в опросе может быть не указана. Если не у всех вопросов указана или указана неверно, то генерация на бэкенде
    position: Optional[int] = Field(None, ge=1, le=100, description='Порядок отображения варианта ответа')


class QuestionCreate(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000, description="Текст вопроса")
    type: str = Field(..., pattern="^(single_choice|multiple_choice|text|scale)$")
    is_required: Optional[bool] = None
    options: Optional[List[QuestionOptionCreate]] = Field(None, min_length=2, max_length=10,
                                                          description="Варианты ответов (от 2 до 10)")
    # позиция вопроса в опросе может быть не указана. Если не у всех вопросов указана или указана неверно, то генерация на бэкенде
    position: Optional[int] = Field(None, ge=1, le=100, description='Порядок отображения вопроса в опросе (1,2,3, ...')

    @model_validator(mode="after")
    def validate_options_consistency(self) -> "QuestionCreate":
        choice_types = ("single_choice", "multiple_choice")
        no_options_types = ("text",)
        if self.type in no_options_types and self.options is not None:
            raise ValueError("Варианты не поддерживаются для текстового вопроса")
        if self.type in choice_types and self.options is None:
            raise ValueError("Для выбора вариантов необходимо указать варианты ответов")
        return self


class PollCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200, description="Название опроса")
    description: Optional[str] = Field(None, max_length=2000, description="Описание опроса")
    questions: list[QuestionCreate] = Field(..., min_length=1, max_length=50)
    # Опциональные настройки (будут использованы дефолты модели, если не переданы)
    status: Optional[str] = Field(default='draft', pattern='^(draft|active|closed)$')
    expires_at: Optional[datetime] = Field(None, description="Дата окончания опроса")  # default null
    is_anonymous: Optional[bool] = None  # default true
    one_response_only: Optional[bool] = None  # default true
    poll_type: Optional[str] = Field(None, pattern="^(corporate|client)$")  # default 'corporate'
    language: Optional[str] = Field(None, pattern="^(ru|en)$")  # default 'ru'
    max_participants: Optional[int] = Field(None, ge=1)  #
    show_progress: Optional[bool] = None  # default true
    notify_on_response: Optional[bool] = None  # default false
    generated_by_ai: Optional[bool] = None  # default false
    ai_generation_prompt: Optional[str] = None  # default null
    target_participants: Optional[int] = None  # default null

    @model_validator(mode="after")
    def validate_expires_at(self) -> "PollCreate":
        if self.expires_at:
            # 1. Приводим к naive datetime, т.к. БД не хранит таймзону
            if self.expires_at.tzinfo is not None:
                self.expires_at = self.expires_at.replace(tzinfo=None)
            # 2. Сравниваем с текущим временем (тоже приводим к naive)
            now_naive = datetime.now(timezone.utc).replace(tzinfo=None)
            if self.expires_at <= now_naive:
                raise ValueError("Дата окончания опроса должна быть строго в будущем")
        return self


class PollCreatedResponse(BaseModel):
    id: int = Field(..., description="Уникальный идентификатор опроса")
    title: str = Field(..., description="Название опроса")
    status: str = Field(..., description="Статус опроса")
    vote_link: str = Field(..., description="Ссылка на опрос для голосования")

    class Config:
        from_attributes = True  # для совместимости с ORM-объектами, если понадобится


class OptionResponse(BaseModel):
    id: int
    text: str
    position: int
    model_config = ConfigDict(from_attributes=True)


class QuestionResponse(BaseModel):
    id: int
    text: str
    type: str
    is_required: bool
    position: int
    options: List[OptionResponse]
    model_config = ConfigDict(from_attributes=True)


class PollDetailResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    status: str
    created_at: datetime
    published_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_anonymous: Optional[bool] = None
    one_response_only: Optional[bool] = None
    poll_type: Optional[str] = None
    language: Optional[str] = None
    max_participants: Optional[int] = None
    show_progress: Optional[bool] = None
    notify_on_response: Optional[bool] = None
    questions: List[QuestionResponse]

    model_config = ConfigDict(from_attributes=True)


class OptionResult(BaseModel):
    question: str = Field(..., description="Текст вопроса")
    question_position: int = Field(..., description="Позиция вопроса")
    option: str = Field(..., description="Текст варианта ответа")
    option_position: int = Field(..., description="Позиция варианта ответа")
    votes: int = Field(..., description="Количество голосов")
    percentage: float = Field(..., description="Процент голосов")


class AverageValue(BaseModel):
    question: str = Field(..., description="Текст вопроса")
    question_position: int = Field(..., description="Позиция вопроса")
    option: str = Field(default="Средний рейтинг", description="Текст метрики")
    avg_value: float = Field(..., description="Среднее значение")


class PollResponse(BaseModel):
    id: int = Field(..., description="Уникальный идентификатор опроса")
    title: str = Field(..., description="Название опроса")
    options: List[str] = Field(..., description="Список вариантов")
    description: Optional[str] = Field(None, description="Описание опроса")
    created_at: datetime = Field(..., description="Дата и время создания")
    votes: List[OptionResult] = Field(..., description="Словарь с подсчётом голосов")


class PollResultsResponse(BaseModel):
    id: int = Field(..., description="Уникальный идентификатор опроса")
    title: str = Field(..., description="Название опроса")
    options: List[str] = Field(..., description="Список вариантов")
    description: Optional[str] = Field(None, description="Описание опроса")
    created_at: datetime = Field(..., description="Дата и время создания")
    total_votes: int = Field(..., description="Общее количество голосов")
    votes: Optional[List[OptionResult]] = Field(..., description="Словарь с подсчётом голосов")
    avg_values: Optional[List[AverageValue]] = Field(..., description="Словарь со средними значениями")
    response_rate: float = Field(..., description="Отклик на опрос")
    avg_completion_time: float = Field(..., description="Среднее время прохождения опроса")


class PollSummary(BaseModel):
    """Краткая информация для списка опросов"""
    id: int = Field(..., description="Уникальный идентификатор опроса")
    title: str = Field(..., description="Название опроса")
    status: str = Field(..., description="Статус опроса")
    created_at: datetime = Field(..., description="Дата и время создания")
    expires_at: Optional[datetime] = Field(default=None, description="Дата окончания опроса")
    total_votes: int = Field(..., description="Общее количество голосов")


class AnswerRequest(BaseModel):
    """Ответ на вопрос"""
    question_id: int = Field(..., description="ID вопроса")
    option_id: int = Field(..., description="ID варианта ответа")
    text_value: Optional[str] = Field(..., description="Текст")

    class Config:
        from_attributes = True


class VoteRequest(BaseModel):
    """Тело запроса для голосования"""
    answers: List[AnswerRequest] = Field(..., description="Полученные ответы от пользователя")


class VoteResponse(BaseModel):
    """Ответ после успешного голосования"""
    poll_id: int = Field(..., description="ID опроса")
    answers_confirmed: List[AnswerRequest] = Field(..., description="Потвержденные ответы от пользователя")
    message: str = Field(..., description="Статусное сообщение")


class PollStatusUpdate(BaseModel):
    """Тело запроса для изменения статуса опроса"""
    status: Literal["draft", "active", "closed"] = Field(..., description="Новый статус опроса (draft, active, closed)"
    )