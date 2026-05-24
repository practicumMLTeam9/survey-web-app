import json
import os
import re
from datetime import datetime
from typing import Dict
from zoneinfo import ZoneInfo
from src.db.models import User

import httpx
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import ValidationError

from src.api_schemas.poll import PollCreate, GeneratePollRequest
from src.security.security import security_scheme, get_current_user
import logging
from src.services.ai_service import ApiLLMService, get_llm_service
from src.api_schemas.ai import LLMRequestParams, Test

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/polls",
                   tags=["AI Generation"],
                   dependencies=[Depends(security_scheme)],  # ← глобальная проверка для всех методов в роутере
                   responses={404: {"description": "Not found"}}, )


@router.post(
    "/generate",
    response_model=PollCreate,
    status_code=status.HTTP_200_OK,
    summary="Сгенерировать опрос с помощью AI",
    description="Вызывает LLM по промпту и возвращает предзаполненную структуру опроса."
)
async def generate_poll_endpoint(
        req: GeneratePollRequest,
        current_user: User = Depends(get_current_user())  # ← если нужна авторизация
):
    return await generate_poll(req)


def _normalize_positions(poll_data: Dict) -> Dict:
    """Гарантирует корректные последовательные позиции вопросов и вариантов."""
    for i, q in enumerate(poll_data.get("questions", []), start=1):
        q["position"] = q.get("position") or i
        if isinstance(q.get("options"), list):
            for j, opt in enumerate(q["options"], start=1):
                opt["position"] = opt.get("position") or j
    return poll_data


def _extract_json_from_llm(raw_text: str) -> Dict:
    """Извлекает JSON из ответа LLM, удаляя markdown-обёртки ```json ... ```"""
    match = re.search(r'```(?:json)?\s*(.*?)\s*```', raw_text, re.DOTALL)
    clean = match.group(1) if match else raw_text
    return json.loads(clean)


async def _call_llm_api(req: GeneratePollRequest) -> dict:
    llm_url = os.getenv("LLM_API_URL", "http://localhost:1234/v1/chat/completions")
    model = os.getenv("LLM_MODEL", "local-model")

    system_prompt = ("""Ты — генератор опросов. Возвращай ТОЛЬКО валидный JSON, строго соответствующий схеме ниже. Никаких пояснений, markdown или комментариев.

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
                     )

    user_prompt = (
        f"Тема: {req.prompt}. "
        f"Количество вопросов: {req.questions_count}. "
        f"Язык: {req.language}. Тип опроса: {req.poll_type}. "
        f"Анонимный: {req.is_anonymous}. Один ответ на пользователя: {req.one_response_only}. "
        f"Разрешённые типы вопросов: {req.allowed_question_types}."
    )

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            llm_url,
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.7,
                "response_format": {"type": "json_object"}
            }
        )
        resp.raise_for_status()
        return _extract_json_from_llm(resp.json()["choices"][0]["message"]["content"])


async def generate_poll(req: GeneratePollRequest):
    """
    Генерирует черновик опроса через LLM и возвращает валидированную схему PollCreate.
    Фронтенд должен отредактировать и отправить на POST /.
    """
    try:
        # 1. Запрос к LLM
        llm_data = await _call_llm_api(req)

        # Защита: LLM иногда возвращает list или строку вместо dict
        if not isinstance(llm_data, dict):
            raise ValueError("LLM вернул не JSON-объект")

        # 2. Дополняем дефолтами из запроса, если LLM пропустил
        llm_data.setdefault("status", "draft")
        llm_data.setdefault("is_anonymous", req.is_anonymous)
        llm_data.setdefault("one_response_only", req.one_response_only)
        llm_data.setdefault("poll_type", req.poll_type)
        llm_data.setdefault("language", req.language)

        # 3. Нормализация позиций
        _normalize_positions(llm_data)

        # 4. Безопасная обработка expires_at
        if llm_data.get("expires_at"):
            try:
                exp_str = str(llm_data["expires_at"])
                exp_dt = datetime.fromisoformat(exp_str)
                if exp_dt.tzinfo is None:
                    exp_dt = exp_dt.replace(tzinfo=ZoneInfo("Europe/Moscow"))
                if exp_dt <= datetime.now(exp_dt.tzinfo):
                    llm_data["expires_at"] = None
            except Exception:
                llm_data["expires_at"] = None

        # 5. Финальная валидация через вашу схему
        return PollCreate(**llm_data)

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"LLM вернул некорректный JSON: {str(e)}")
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=f"Ошибка структуры опроса: {e.errors()}")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Ошибка LLM API: {e.response.text}")
    except httpx.RequestError as e:  # Таймауты, DNS, обрыв соединения
        raise HTTPException(status_code=504, detail=f"Не удалось связаться с LLM: {e}")
    except Exception:  # noqa: BLE001 (допустимо на границе внешних API)
        logger.exception("Непредвиденная ошибка при генерации опроса через LLM")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка генерации. Попробуйте позже или измените промпт."
        )


@router.post("/test_ai")
async def test_ai(
    prompt: str,
    llm_service: ApiLLMService = Depends(get_llm_service)
):
    params = LLMRequestParams(
        prompt=prompt,
        model="baidu/cobuddy:free",
        temperature=0.2,
        max_tokens=2000,
        response_model=Test,
        response_format={"type": "json_object"}
    )
    
    system_prompt = "Верни ответ в формате JSON"
    
    result = await llm_service.generate_ai(params, system_prompt)
    return result