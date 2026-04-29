from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime
from typing import List, Optional, Dict

# ─── Вспомогательные схемы ───
class QuestionOptionCreate(BaseModel):
    text: str = Field(..., min_length=1, max_length=500, description="Текст варианта ответа")

class QuestionCreate(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000, description="Текст вопроса")
    type: str = Field(..., pattern="^(single_choice|multiple_choice|text|rating)$")
    is_required: Optional[bool] = True
    options: List[str] = Field(..., min_length=2, max_length=10, description="Варианты ответов (от 2 до 10)")
    # позиция может быть не указана (автогенерация на бэкенде):
    position: Optional[int] = Field(None, ge=0, le=100, description='Порядок отображения вопроса в опросе')

    @field_validator('position')
    @classmethod
    def validate_position(cls, v):
        if v is not None and v < 0:
            raise ValueError('Позиция не может быть отрицательной')
        return v

    @model_validator(mode="after")
    def validate_options_consistency(self) -> "QuestionCreate":
        choice_types = ("single_choice", "multiple_choice")
        no_options_types = ("text", "rating")

        if self.type in no_options_types and self.options is not None:
            raise ValueError("Варианты ответов не поддерживаются для этого типа вопроса")
        if self.type in choice_types and self.options is None:
            raise ValueError("Для вопросов с выбором необходимо указать варианты ответов")
        return self

# ─── Основная схема создания ───
class PollCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200, description="Название опроса")
    description: Optional[str] = Field(None, max_length=2000, description="Описание опроса")
    questions: list[QuestionCreate] = Field(..., min_length=1, max_length=50)

    # Опциональные настройки (будут использованы дефолты модели, если не переданы)
    is_anonymous: Optional[bool] = None         # default true
    one_response_only: Optional[bool] = None    # default true
    poll_type: Optional[str] = Field(None, pattern="^(corporate|client)$") # default 'corporate'
    language: Optional[str] = Field(None, pattern="^(ru|en|de)$") # default
    max_participants: Optional[int] = Field(None, ge=1)    # ???
    show_progress: Optional[bool] = None        # default true
    notify_on_response: Optional[bool] = None   # default false
    generated_by_ai: Optional[bool] = None      # default false
    ai_generation_prompt: Optional[str] = None # ???
    target_participants: Optional[int] = None # ???

class PollCreatedResponse(BaseModel):
    id: str = Field(..., description="Уникальный идентификатор опроса")
    title: str = Field(..., description="Название опроса")
    vote_link: str = Field(..., description="Ссылка на опрос для голосования")

    class Config:
        from_attributes = True  # для совместимости с ORM-объектами, если понадобится

class OptionResult(BaseModel):
    option: str = Field(..., description="Текст варианта ответа")
    votes: int = Field(..., description="Количество голосов")
    percentage: float = Field(..., description="Процент голосов")

class PollResponse(BaseModel):
    id: str = Field(..., description="Уникальный идентификатор опроса")
    title: str = Field(..., description="Название опроса")
    options: List[str] = Field(..., description="Список вариантов")
    description: Optional[str] = Field(None, description="Описание опроса")
    created_at: datetime = Field(..., description="Дата и время создания")
    votes: Dict[str, int] = Field(..., description="Словарь с подсчётом голосов")

class PollResultsResponse(BaseModel):
    id: str = Field(..., description="Уникальный идентификатор опроса")
    title: str = Field(..., description="Название опроса")
    results: List[OptionResult] = Field(..., description="Список результатов по вариантам")
    total_votes: int = Field(..., description="Общее количество голосов")
    created_at: datetime = Field(..., description="Дата и время создания")

class PollSummary(BaseModel):
    """Краткая информация для списка опросов"""
    id: str = Field(..., description="Уникальный идентификатор опроса")
    title: str = Field(..., description="Название опроса")
    created_at: datetime = Field(..., description="Дата и время создания")
    total_votes: int = Field(..., description="Общее количество голосов")

class PollDetailResponse(BaseModel):
    """Детальный опрос"""
    id: str = Field(..., description="Уникальный идентификатор опроса")
    title: str = Field(..., description="Название опроса")
    description: Optional[str] = Field(None, description="Описание опроса")
    options: List[str] = Field(..., description="Список вариантов")
    created_at: datetime = Field(..., description="Дата и время создания")
    # results: List[OptionResult] = Field(..., description="Список результатов по вариантам")
    total_votes: int = Field(..., description="Общее количество голосов")

class VoteRequest(BaseModel):
    """Тело запроса для голосования"""
    option: str = Field(..., min_length=1, max_length=100, description="Выбранный вариант ответа")

class VoteResponse(BaseModel):
    """Ответ после успешного голосования"""
    poll_id: str = Field(..., description="ID опроса")
    voted_option: str = Field(..., description="Выбранный вариант")
    total_votes: int = Field(..., description="Общее количество голосов после обновления")
    message: str = Field(..., description="Статусное сообщение")