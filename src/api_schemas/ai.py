from typing import Optional, Dict, Type, List, Any
from pydantic import BaseModel, Field

class LLMRequestParams(BaseModel):
    """Параметры запроса к LLM"""
    prompt: str = Field(..., description="Промпт для генерации")
    model: str = Field(default="openrouter/free", description="Модель LLM")
    response_model: Optional[Type[BaseModel]] = Field(default=None, description="Pydantic модель для структурированного вывода")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Креативность ответа")
    max_tokens: int = Field(default=2000, ge=1, description="Максимальное количество токенов")
    top_p: float = Field(default=1.0, ge=0.0, le=1.0, description="Nucleus sampling")
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0, description="Штраф за частоту упоминания")
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0, description="Штраф за новые темы")
    stop: Optional[List[str]] = Field(default=None, description="Стоп-последовательности")
    response_format: Optional[Dict[str, str]] = Field(default=None, description="Формат ответа (например, {'type': 'json_object'})")
    seed: Optional[int] = Field(default=None, description="Seed для воспроизводимости результатов")
    top_k: Optional[int] = Field(default=None, ge=1, le=200, description="Top-K sampling")
    repetition_penalty: Optional[float] = Field(default=None, ge=0.0, le=2.0, description="Штраф за повторения")


class LLMResponse(BaseModel):
    """Ответ от LLM"""
    content: str = Field(..., min_length=1, description="Сгенерированный текст")
    model: str = Field(..., description="Использованная модель")
    finish_reason: Optional[str] = Field(None, description="Причина завершения генерации")
    usage: Dict[str, Any] = Field(default_factory=dict, description="Использование токенов")

class Test(BaseModel):
    test: str = Field(..., min_length=1, description="Сгенерированный текст")