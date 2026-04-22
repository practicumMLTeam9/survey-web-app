from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime

class PollCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100, description="Название опроса")
    options: List[str] = Field(..., min_length=2, max_length=10, description="Варианты ответов")
    description: Optional[str] = Field(None, max_length=500, description="Описание (опционально)")

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