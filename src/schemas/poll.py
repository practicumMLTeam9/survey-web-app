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