from typing import Optional, Dict, Type, List, Any, Union
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


class SentimentCount(BaseModel):
    count: int = Field(..., description="Количество ответов")
    percentage: float = Field(..., description="Процент ответов")


class Sentiment(BaseModel):
    positive: SentimentCount = Field(..., description="Положительные ответы")
    neutral: SentimentCount = Field(..., description="Нейтральные ответы")
    negative: SentimentCount = Field(..., description="Негативные ответы")
    conclusion: str = Field(..., description="Вывод по тональности")


class Theme(BaseModel):
    theme: str = Field(..., description="Название темы")
    count: int = Field(..., description="Количество упоминаний")
    quotes: List[str] = Field(..., description="Цитаты по теме")


class Insight(BaseModel):
    text: str = Field(..., description="Текст инсайта")
    type: str = Field(..., description="Тип инсайта (critical/warning/positive)")
    emoji: str = Field(..., description="Эмодзи для визуализации")
    color: str = Field(..., description="Цвет в HEX формате")


class Recommendation(BaseModel):
    text: str = Field(..., description="Текст рекомендации")
    priority: str = Field(..., description="Приоритет (high/medium/low)")
    priority_color: str = Field(..., description="Цвет приоритета в HEX формате")


class AnalyticsResponse(BaseModel):
    """Модель для агрегированного аналитического ответа"""
    summary: str = Field(..., description="Краткое резюме аналитики")
    sentiment: Sentiment = Field(..., description="Анализ тональности")
    themes: List[Theme] = Field(default_factory=list, description="Темы из текстовых ответов")
    insights: List[Insight] = Field(default_factory=list, description="Ключевые инсайты")
    recommendations: List[Recommendation] = Field(default_factory=list, description="Рекомендации")
    aggregated_values: Union[List[Dict[str, Any]], Dict[str, Any]] = Field(default_factory=dict, description="Агрегированные значения из БД")