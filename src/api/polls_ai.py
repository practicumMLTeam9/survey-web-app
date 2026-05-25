import os
import json
import logging
import time
import uuid
from datetime import datetime
from typing import Dict
from zoneinfo import ZoneInfo

from fastapi import APIRouter, HTTPException, Depends, status, Body
from pydantic import ValidationError

from src.api_schemas.poll import PollCreate, GeneratePollRequest
from src.api_schemas.ai import LLMRequestParams, Test
from src.db.models import User, AiRequest
from src.security.security import security_scheme, get_current_user
from src.services.ai_service import ApiLLMService, get_llm_service
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.async_session import get_db as get_assync_db

DEFAULT_MODEL = os.getenv("DEFAULT_LLM_MODEL", "baidu/cobuddy:free")
ALLOWED_MODELS = {
    "baidu/cobuddy:free",
    "google/gemini-2.0-flash-lite:free",
    "qwen/qwen-2.5-7b-instruct:free",
    "meta-llama/llama-3.2-3b-instruct:free",
    "mistralai/mistral-7b-instruct:free",
}

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
    prefix="/api/v1/ai",
    tags=["AI Generation"],
    dependencies=[Depends(security_scheme)],
    responses={404: {"description": "Not found"}},
)


def _normalize_positions(poll_data: Dict) -> Dict:
    """Гарантирует корректные последовательные позиции вопросов и вариантов."""
    for i, q in enumerate(poll_data.get("questions", []), start=1):
        q["position"] = q.get("position") or i
        if isinstance(q.get("options"), list):
            for j, opt in enumerate(q["options"], start=1):
                opt["position"] = opt.get("position") or j
    return poll_data


@router.post(
    "/generate_poll",
    response_model=PollCreate,
    status_code=status.HTTP_200_OK,
    summary="Сгенерировать опрос с помощью AI",
    description="Вызывает LLM по промпту и возвращает предзаполненную структуру опроса."
)
async def generate_poll(
        req: GeneratePollRequest,
        current_user: User = Depends(get_current_user()),
        db: AsyncSession = Depends(get_assync_db),
        llm_service: ApiLLMService = Depends(get_llm_service)
):
    """
    Генерирует черновик опроса через LLM, логирует запрос в AiRequest,
    возвращает session_token для связи с финальным опросом и возвращает валидированную схему PollCreate.
    Фронтенд должен отредактировать и отправить на POST /.
    """
    # 1. Проверка модели
    if req.model not in ALLOWED_MODELS:
        raise HTTPException(
            status_code=400,
            detail=f"Модель '{req.model}' не поддерживается. Доступны: {', '.join(ALLOWED_MODELS)}")

    session_token = str(uuid.uuid4())
    start_time = time.perf_counter()
    try:
        user_prompt = (
            f"Тема: {req.prompt}. "
            f"Количество вопросов: {req.questions_count}. "
            f"Язык: {req.language}. Тип опроса: {req.poll_type}. "
            f"Анонимный: {req.is_anonymous}. Один ответ на пользователя: {req.one_response_only}. "
            f"Разрешённые типы вопросов: {req.allowed_question_types}."
        )

        # Используем модель из запроса
        llm_params = LLMRequestParams(
            prompt=user_prompt,
            model=req.model,
            temperature=0.1,
            max_tokens=2000,
            top_p=0.9,
            response_format={"type": "json_object"})

        # 2. Вызов LLM
        llm_data = await llm_service.generate_ai(llm_params, SYSTEM_PROMPT_GENERATE)
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # 3. Защита: LLM иногда возвращает list или строку вместо dict
        if not isinstance(llm_data, dict):
            raise ValueError("LLM вернул не JSON-объект")

        # 4. Постобработка данных (нормализация, дефолты, expires_at)
        llm_data.setdefault("generated_by_ai", True)
        llm_data.setdefault("status", "draft")
        llm_data.setdefault("is_anonymous", req.is_anonymous)
        llm_data.setdefault("one_response_only", req.one_response_only)
        llm_data.setdefault("poll_type", req.poll_type)
        llm_data.setdefault("language", req.language)

        _normalize_positions(llm_data)

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

        llm_data["ai_request_session_token"] = session_token
        llm_data["ai_generation_prompt"] = req.prompt

        # 5. Сбор метрик ПОСЛЕ постобработки, но ДО финальной валидации
        is_valid_json: bool = True
        is_valid_schema: bool = False
        error_type: str | None = None
        estimated_tokens: int | None = len(json.dumps(llm_data, ensure_ascii=False)) // 4

        poll_create_obj: PollCreate | None = None
        try:
            # Валидируем финальные, обработанные данные
            poll_create_obj = PollCreate(**llm_data)
            is_valid_schema = True
        except ValidationError as e:
            is_valid_schema = False
            error_type = "schema_validation_failed"
        except Exception as e:
            error_type = f"unexpected: {str(e)[:30]}"

        # 6. Логирование в AiRequest (poll_id=None, так как опрос ещё не создан)
        ai_request = AiRequest(
            user_id=current_user.id,
            poll_id=None,
            request_type="generate_poll",
            model=req.model,
            latency_ms=latency_ms,
            session_token=session_token,
            # Явно передаём значения, переопределяя server_default для предсказуемости
            is_valid_json=is_valid_json,
            is_valid_schema=is_valid_schema,
            error_type=error_type,
            estimated_tokens=estimated_tokens,
            user_edited_draft=False  # При генерации черновик ещё не правился
        )
        db.add(ai_request)

        # Попытка сохранить метрики. Если база "отвалилась" — просто пропускаем.
        try:
            await db.commit()
        except Exception:
            # Если соединение закрылось (например, из-за долгого ожидания),
            # мы просто откатываем транзакцию, чтобы не сломать ответ пользователю.
            await db.rollback()
            logger.warning("Не удалось сохранить метрики: соединение с БД разорвано.")

        # 7. Если схема не прошла валидацию, возвращаем 422, но метрика уже сохранена
        if not is_valid_schema:
            raise HTTPException(
                status_code=422,
                detail="Сгенерированный JSON не соответствует схеме PollCreate")

        # 8. Возврат уже валидированного объекта (без повторной валидации)
        llm_data["ai_generation_prompt"] = req.prompt
        llm_data["ai_request_session_token"] = session_token

        return poll_create_obj  # Используем объект, созданный при валидации

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"LLM вернул некорректный JSON: {str(e)}")
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=f"Ошибка структуры опроса: {e.errors()}")
    except HTTPException:
        raise
    except Exception:  # noqa: BLE001
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
