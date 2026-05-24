import os
import json
import logging
from datetime import datetime
from typing import Dict
from zoneinfo import ZoneInfo

from fastapi import APIRouter, HTTPException, Depends, status, Body
from pydantic import ValidationError

from src.api_schemas.poll import PollCreate, GeneratePollRequest
from src.api_schemas.ai import LLMRequestParams, Test
from src.db.models import User
from src.security.security import security_scheme, get_current_user
from src.services.ai_service import ApiLLMService, get_llm_service

DEFAULT_MODEL = os.getenv("DEFAULT_LLM_MODEL", "baidu/cobuddy:free")
SYSTEM_PROMPT_GENERATE = """Ты — генератор опросов. Возвращай ТОЛЬКО валидный JSON, строго соответствующий схеме ниже. Никаких пояснений, markdown или комментариев.

{
  "title": "Название опроса (3-200 символов)",
  "description": "Краткое описание или null",
  "status": "draft",
  "is_anonymous": true,
  "one_response_only": true,
  "poll_type": "corporate",
  "language": "ru",
  "questions": [
    {
      "text": "Текст вопроса (до 1000 символов)",
      "type": "single_choice | multiple_choice | text | scale",
      "is_required": true,
      "options": [{"text": "Вариант ответа (до 500 символов)", "position": 1}]
    }
  ]
}

ПРАВИЛА:
1. Для type="text" НЕ добавляй поле options.
2. Для type="single_choice|multiple_choice|scale" добавь 2-5 options.
3. Типы вопросов используй ТОЛЬКО из переданного списка разрешённых.
4. Поле position в вопросах и вариантах можно опустить (бэкенд проставит автоматически).
5. Не добавляй поля, которых нет в схеме. Не генерируй expires_at, если не просили."""

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/polls",
    tags=["AI Generation"],
    dependencies=[Depends(security_scheme)],
    responses={404: {"description": "Not found"}},
)


# ─── Вспомогательные функции (бизнес-логика, не зависит от LLM) ───
def _normalize_positions(poll_data: Dict) -> Dict:
    """Гарантирует корректные последовательные позиции вопросов и вариантов."""
    for i, q in enumerate(poll_data.get("questions", []), start=1):
        q["position"] = q.get("position") or i
        if isinstance(q.get("options"), list):
            for j, opt in enumerate(q["options"], start=1):
                opt["position"] = opt.get("position") or j
    return poll_data


# ─── Эндпоинт генерации опроса ───
@router.post(
    "/generate",
    response_model=PollCreate,
    status_code=status.HTTP_200_OK,
    summary="Сгенерировать опрос с помощью AI",
    description="Вызывает LLM по промпту и возвращает предзаполненную структуру опроса."
)
async def generate_poll_endpoint(
        req: GeneratePollRequest,
        current_user: User = Depends(get_current_user()),
        llm_service: ApiLLMService = Depends(get_llm_service)
):
    """
    Генерирует черновик опроса через LLM и возвращает валидированную схему PollCreate.
    Фронтенд должен отредактировать и отправить на POST /.
    """
    try:
        # 1. Формируем параметры запроса к LLM
        user_prompt = (
            f"Тема: {req.prompt}. "
            f"Количество вопросов: {req.questions_count}. "
            f"Язык: {req.language}. Тип опроса: {req.poll_type}. "
            f"Анонимный: {req.is_anonymous}. Один ответ на пользователя: {req.one_response_only}. "
            f"Разрешённые типы вопросов: {req.allowed_question_types}."
        )

        llm_params = LLMRequestParams(
            prompt=user_prompt,
            model=DEFAULT_MODEL,
            temperature=0.1,  # Возможно уменьшить до 0.1 для строгого JSON
            max_tokens=2000,
            top_p=0.9,
            response_format={"type": "json_object"}
        )

        # 2. Вызов LLM через сервис
        llm_data = await llm_service.generate_ai(llm_params, SYSTEM_PROMPT_GENERATE)

        # 3. Защита: LLM иногда возвращает list или строку вместо dict
        if not isinstance(llm_data, dict):
            raise ValueError("LLM вернул не JSON-объект")

        # 4. Дополняем дефолтами из запроса, если LLM пропустил
        llm_data.setdefault("status", "draft")
        llm_data.setdefault("is_anonymous", req.is_anonymous)
        llm_data.setdefault("one_response_only", req.one_response_only)
        llm_data.setdefault("poll_type", req.poll_type)
        llm_data.setdefault("language", req.language)

        # 5. Нормализация позиций
        _normalize_positions(llm_data)

        # 6. Безопасная обработка expires_at
        if llm_data.get("expires_at"):
            try:
                exp_str = str(llm_data["expires_at"])
                exp_dt = datetime.fromisoformat(exp_str)
                if exp_dt.tzinfo is None:
                    exp_dt = exp_dt.replace(tzinfo=ZoneInfo("Europe/Moscow"))
                if exp_dt <= datetime.now(exp_dt.tzinfo):
                    llm_data["expires_at"] = None  # LLM часто генерирует прошлые даты → сбрасываем
            except Exception:
                llm_data["expires_at"] = None

        # 7. Финальная валидация через API схему
        return PollCreate(**llm_data)

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"LLM вернул некорректный JSON: {str(e)}")
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=f"Ошибка структуры опроса: {e.errors()}")
    except HTTPException:
        # Пробрасываем уже оформленные ошибки сервиса (401, 502, 504)
        raise
    except Exception:  # noqa: BLE001 (допустимо на границе внешних API)
        logger.exception("Непредвиденная ошибка при генерации опроса через LLM")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка генерации. Попробуйте позже или измените промпт."
        )


# ─── Тестовый эндпоинт (для отладки) ───
@router.post("/test_ai", response_model=Test)
async def test_ai(
        prompt: str = Body(..., embed=True, description="Промпт для теста"),
        llm_service: ApiLLMService = Depends(get_llm_service)
):
    """Тестовый вызов LLM с возвратом структурированного ответа"""
    params = LLMRequestParams(
        prompt=prompt,
        model=DEFAULT_MODEL,
        temperature=0.2,  # Возможно уменьшить до 0.1 для строгого JSON
        max_tokens=500,
        response_model=Test,
        response_format={"type": "json_object"}
    )

    system_prompt = "Верни ответ строго в формате JSON без пояснений."

    result = await llm_service.generate_ai(params, system_prompt)
    return result