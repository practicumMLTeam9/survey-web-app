from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime

class PollCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100, description="Название опроса")
    options: List[str] = Field(..., min_length=2, max_length=10, description="Варианты ответов")
    description: Optional[str] = Field(None, max_length=500, description="Описание (опционально)")

class OptionResult(BaseModel):
    option: str
    votes: int
    percentage: float

class PollResponse(BaseModel):
    id: str
    title: str
    options: List[str]
    description: Optional[str]
    created_at: datetime
    votes: Dict[str, int]

class PollResultsResponse(BaseModel):
    id: str
    title: str
    results: List[OptionResult]
    total_votes: int
    created_at: datetime

class PollSummary(BaseModel):
    """Краткая информация для списка опросов"""
    id: str
    title: str
    created_at: datetime
    total_votes: int

class PollDetailResponse(BaseModel):
    """Детальный опрос"""
    id: str
    title: str
    description: Optional[str]
    options: List[str]
    created_at: datetime
    results: List[OptionResult]
    total_votes: int

class VoteRequest(BaseModel):
    """Тело запроса для голосования"""
    option: str = Field(..., min_length=1, max_length=100, description="Выбранный вариант ответа")

class VoteResponse(BaseModel):
    """Ответ после успешного голосования"""
    poll_id: str
    voted_option: str
    total_votes: int
    message: str