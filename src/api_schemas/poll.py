from pydantic import BaseModel, Field, model_validator, ConfigDict, field_validator
from datetime import datetime
from typing import List, Optional, Literal, Any
from zoneinfo import ZoneInfo


# ─── Вспомогательные схемы ───
class QuestionOptionCreate(BaseModel):
    text: str = Field(..., min_length=1, max_length=500,
                      description="Текст варианта ответа")  # позиция вопроса в опросе может быть не указана. Если не у всех вопросов указана или указана неверно, то генерация на бэкенде
    position: Optional[int] = Field(None, ge=1, le=100, description='Порядок отображения варианта ответа')


class QuestionCreate(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000, description="Текст вопроса")
    type: str = Field(..., pattern="^(single_choice|multiple_choice|text|scale)$")
    is_required: Optional[bool] = None
    position: Optional[int] = Field(None, ge=1, le=100, description='Порядок отображения вопроса')
    options: Optional[List["QuestionOptionCreate"]] = Field(
        None,
        description="Варианты ответов (от 2 до 10 для choice/scale)"
    )

    @field_validator('options', mode='before')
    @classmethod
    def normalize_empty_list(cls, v: Any) -> Optional[List]:
        # [] превращаем в None, чтобы не триггерить min_length валидацию поля
        return None if v == [] else v

    @model_validator(mode='after')
    def validate_options_consistency(self) -> "QuestionCreate":
        if self.type == "text" and self.options is not None:
            raise ValueError("Варианты не поддерживаются для текстового вопроса")

        if self.type in ("single_choice", "multiple_choice", "scale"):
            if self.options is None or len(self.options) < 2:
                raise ValueError("Для выбора/шкалы необходимо минимум 2 варианта ответов")
            if len(self.options) > 10:
                raise ValueError("Максимум 10 вариантов ответов")

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
    target_participants: Optional[int] = None  # default null
    # Служебные поля для связи с AI-генерацией (заполняются фронтендом)
    ai_request_session_token: Optional[str] = Field(None, description="Токен сессии AI-генерации")
    ai_generation_prompt: Optional[str] = Field(None, description="Исходный промпт для истории чата")

    @model_validator(mode="after")
    def validate_expires_at(self) -> "PollCreate":
        if self.expires_at:
            # Если время пришло без пояса (naive), считаем, что это время Москвы (UTC+3)
            if self.expires_at.tzinfo is None:
                self.expires_at = self.expires_at.replace(tzinfo=ZoneInfo("Europe/Moscow"))

            # Валидация в одном часовом поясе
            if self.expires_at <= datetime.now(self.expires_at.tzinfo):
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
    type: str = Field(..., description="Тип опроса")
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


class GeneratePollRequest(BaseModel):
    prompt: str = Field(..., min_length=10, max_length=2000, description="Описание опроса для LLM")
    poll_type: Literal["corporate", "client"] = Field(..., description="Тип опроса: corporate или client")
    language: Literal["ru", "en"] = Field(..., description="Язык опроса: ru или en")
    questions_count: int = Field(..., ge=1, le=10, description="Точное количество вопросов для генерации")
    allowed_question_types: Optional[List[Literal["single_choice", "multiple_choice", "scale", "text"]]] = Field(
        default_factory=lambda: ["single_choice", "multiple_choice", "scale", "text"]
    )
    is_anonymous: bool = Field(True)
    one_response_only: bool = Field(True)