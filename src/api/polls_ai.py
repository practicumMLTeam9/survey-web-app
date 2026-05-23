import json
import os
import re
from datetime import datetime
from typing import Dict
from zoneinfo import ZoneInfo

import httpx
from fastapi import APIRouter, HTTPException, Depends
from pydantic import ValidationError

from src.api_schemas.poll import PollCreate, GeneratePollRequest
from src.security.security import security_scheme

router = APIRouter(prefix="/api/v1/polls",
                   tags=["AI Generation"],
                   dependencies=[Depends(security_scheme)],  # ← глобальная проверка для всех методов в роутере
                   responses={404: {"description": "Not found"}}, )


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

    system_prompt = (
        "Ты — генератор опросов. Возвращай ТОЛЬКО валидный JSON без лишних комментариев. "
        "Следуй схеме PollCreate: title, description, questions[]. "
        "Каждый вопрос: text, type (только из разрешённых), is_required, options[] (если type != text), position. "
        "Варианты: text, position. Для 'text' не добавляй options. Позиции можно опустить."
    )

    user_prompt = (
        f"Тема: {req.prompt}. Язык: {req.language}. Тип: {req.poll_type}. "
        f"Вопросов: ~{req.questions_count}. Анонимный: {req.is_anonymous}. "
        f"Один ответ: {req.one_response_only}. Разрешённые типы: {req.allowed_question_types}."
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

        # 2. Дополняем дефолтами из запроса, если LLM пропустил
        llm_data.setdefault("status", "draft")
        llm_data.setdefault("is_anonymous", req.is_anonymous)
        llm_data.setdefault("one_response_only", req.one_response_only)
        llm_data.setdefault("poll_type", req.poll_type)
        llm_data.setdefault("language", req.language)

        # 3. Нормализация позиций (ваше требование)
        _normalize_positions(llm_data)

        # 4. Безопасная обработка expires_at (согласно вашему фиксу часовых поясов)
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

        # 5. Финальная валидация через вашу существующую схему
        return PollCreate(**llm_data)

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"LLM вернул некорректный JSON: {str(e)}")
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=f"Ошибка структуры опроса: {e.errors()}")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Ошибка LLM API: {e.response.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка генерации: {str(e)}")
