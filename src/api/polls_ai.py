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

from src.api_schemas.poll import PollCreate, GeneratePollRequest, PollResultsResponse, GenerateAnalyticsRequest
from src.api_schemas.ai import LLMRequestParams, Test, AnalyticsResponse
from src.db.models import User, AiRequest
from src.security.security import security_scheme, get_current_user
from src.services.ai_service import ApiLLMService, get_llm_service
from src.services.poll_service import get_text_answers, get_aggregate_val
from src.db.models import AiSummary, AiRequest
import json
from src.db.async_session import get_db as get_assync_db
from sqlalchemy.ext.asyncio import AsyncSession
from math import ceil
import asyncio
import time

DEFAULT_MODEL = os.getenv("DEFAULT_LLM_MODEL", "openrouter/owl-alpha")
ALLOWED_MODELS = {
    "openrouter/owl-alpha",
    "google/gemini-2.0-flash-lite:free",
    "qwen/qwen-2.5-7b-instruct:free",
    "meta-llama/llama-3.2-3b-instruct:free",
    "mistralai/mistral-7b-instruct:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
    "google/gemma-4-26b-a4b-it:free",
    "qwen/qwen3-next-80b-a3b-instruct:free",
    "deepseek/deepseek-v4-flash:free",
    "openrouter/owl-alpha",
    "liquid/lfm-2.5-1.2b-thinking:free"
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






SYSTEM_PROPMT_ANALYTICS = """
Ты — AI-аналитик платформы для проведения опросов. Твоя задача — проанализировать результаты опроса и сгенерировать строго структурированный JSON-отчёт на русском языке для отображения в веб-интерфейсе.


Критические требования (обязательны к соблюдению)
1.  Строгая структура ответа: Твой ответ должен быть исключительно валидным JSON-объектом. 
Никакого текста до или после JSON. Не используй Markdown-обёртку.
2.  Запрет на выдумки: Категорически запрещено придумывать имена, названия компаний, локации или цифры, отсутствующие во входных данных. 
Если данных для какого-либо блока недостаточно (например, нет текстовых ответов или шкал), заполни соответствующие поля пустыми массивами или нулевыми значениями, но структуру JSON сохрани полностью. 
В поле вывода в таких случаях пиши: "Недостаточно данных для анализа".
3.  Палитра и оформление: Строго используй указанные ниже обозначения для цветов и иконок, чтобы фронтенд мог их корректно отобразить. 
Не используй другие emoji и названия цветов.
"""


START_PROMPT_ANALYTICS = """
Входные данные
Ты получишь JSON-объект со следующими полями:
- `title`: строка, название опроса.
- `description`: строка или null, описание опроса.
- `language` : язык опроса.
- `total_votes`: целое число, общее количество участников опроса.
- `votes`: список объектов вида `{"question_id","question_votes":["option": "string", "count": int}`, ...] или null}, распределение голосов по вариантам.
- `avg_values`: список объектов вида {"option": "string", "avg_value": float}, ...` или null, средние оценки по шкале (если применимо).
- `response_rate`: число с плавающей точкой, доля ответивших (от 0 до 1).
- `avg_completion_time`: число с плавающей точкой, среднее время заполнения в секундах.
- `answers_list`: список строк, открытые текстовые ответы респондентов.


Схема ответа (JSON Schema)
Сгенерируй JSON строго по следующей схеме:
{
  "summary": "string (4-5 предложений с основными выводами)",


  Валидация тональности: Проанализируй каждый элемент из `text_answers`. 
Количество ответов, отнесённых к позитивным, нейтральным и негативным, в сумме должно быть строго равно `total_votes`. 
Процентное соотношение должно считаться от `total_votes` и в сумме давать 100%.
  "sentiment": {
    "positive": {"count": "int", "percentage": "float"},
    "neutral": {"count": "int", "percentage": "float"},
    "negative": {"count": "int", "percentage": "float"},
    "conclusion": "string (вывод по тональности, 1 предложение)"
  },

  Валидация тем и цитат: Ты должен выделить ровно 10 ключевых тем из открытых ответов. 
Для каждой темы приведи ровно 3 цитаты. Цитаты должны быть дословными выдержками из `answers_list`.
  "themes": [
    {
      "theme": "string (название темы, 2-4 слова)",
      "count": "int (число упоминаний темы)",
      "quotes": ["string", "string", "string"] // ровно 3 цитаты
    }
    // ... всего должно быть 10 элементов(тем)
  ],

  Логика инсайтов: Должно быть ровно 4 инсайта. Каждый инсайт — одно предложение. 
У каждого инсайта есть оценка: "positive" (зеленый), "warning" (желтый), "critical" (красный) или "neutral". 
Обязательно наличие как минимум одного инсайта типа "positive", одного "critical" и одного "warning".
  "insights": [
    {
      "text": "string (1 предложение)",
      "type": "string (допустимые значения: 'positive', 'warning', 'critical', 'neutral')",
      "emoji": "string (emoji, соответствующий типу)",
      "color": "string (HEX-код цвета, соответствующий типу)"
    }
    // ... всего должно быть 4 элемента
  ],

  Логика рекомендаций: Должно быть ровно 4 рекомендации. 
К каждой указан уровень важности: "high" (красный), "medium" (жёлтый), "low" (зелёный). 
Обязательно должна присутствовать хотя бы одна рекомендация каждого уровня.
  "recommendations": [
    {
      "text": "string (1-2 предложения)",
      "priority": "string (допустимые значения: 'high', 'medium', 'low')",
      "priority_color": "string (HEX-код цвета приоритета)"
    }
    // ... всего должно быть 4 элемента
  ],
}

  Отбор двух ключевых вопросов: Выбрать 2 наиболее важных вопроса.
  "key_questions":{
  "categorical_question": "int"
  "scale_question": "int"
  }

Справочник цветов и Emoji для фронтенда
Используй исключительно следующие значения:

Для инсайтов (insights):
- positive: тип "positive", emoji "✅", цвет "#059669"
- warning: тип "warning", emoji "⚠️", цвет "#D97706"
- critical: тип "critical", emoji "🔴", цвет "#DC2626"
- neutral: тип "neutral", emoji "ℹ️", цвет "#4B5563"

Для рекомендаций (recommendations: priority_color):
- high: цвет "#DC2626"
- medium: цвет "#D97706"
- low: цвет "#059669"


Пример обработки (твоя внутренняя логика)
1.  Получив `answers_list`, классифицируй каждый ответ. 
Если ответов меньше, чем `total_votes`, дозаполни тональность до 100% пропорционально уже классифицированным, но в поле `conclusion` обязательно укажи это допущение.
2.  При выделении 3 тем из `answers_list` сгруппируй семантически близкие ответы. 
Если уникальных ответов меньше 3, создай оставшиеся темы с заглушкой "Прочие аспекты", но с пустыми цитатами. Стремись к тому, чтобы значимые темы были первыми.
3.  Формируя `insights`, базируйся на цифрах (корреляция между данными из `votes`, `avg_values`, `sentiment`). 
Не пиши общих фраз типа "Результаты опроса показали...", пиши конкретно: "82% респондентов негативно оценивают скорость работы, что является критическим сигналом".

Итоговое действие
Сгенерируй итоговый JSON. Проверь его валидность и соответствие всем пунктам перед выводом.
"""

SUMMARY_PROMPT_ANALYTICS = """
Входные данные
Ты получишь массив JSON-объектов с результатами опроса, которые разбиты по частям.
Тебе нужно объединить данные из всех частей и сделать общий вывод по опросу. 


Каждый объект в массиве содержит следующие поля:
{
  "summary": "string (4-5 предложений с основными выводами)",

  Темы, которые были упомянуты участниками в текстовых ответах.
  "themes": [
    {
      "theme": "string (название темы, 2-4 слова)",
      "count": "int (число упоминаний темы)",
      "quotes": ["string", "string", "string"] // ровно 3 цитаты
    }
    // 
  ],

  Инсайты по результатам опроса (4 элемента).
У каждого инсайта есть оценка: "positive" (зеленый), "warning" (желтый), "critical" (красный) или "neutral". 
Обязательно наличие как минимум одного инсайта типа "positive", одного "critical" и одного "warning".
  "insights": [
    {
      "text": "string (1 предложение)",
      "type": "string (допустимые значения: 'positive', 'warning', 'critical', 'neutral')",
      "emoji": "string (emoji, соответствующий типу)",
      "color": "string (HEX-код цвета, соответствующий типу)"
    }
    // ... всего должно быть 4 элемента
  ],

  Рекомендации: Должно быть ровно 4 рекомендации. 
К каждой указан уровень важности: "high" (красный), "medium" (жёлтый), "low" (зелёный). 
Обязательно должна присутствовать хотя бы одна рекомендация каждого уровня.
  "recommendations": [
    {
      "text": "string (1-2 предложения)",
      "priority": "string (допустимые значения: 'high', 'medium', 'low')",
      "priority_color": "string (HEX-код цвета приоритета)"
    }
    // ... всего должно быть 4 элемента
  ],

  Два ключевых вопросов из опроса: Выбрать 2 наиболее важных вопроса.
  "key_questions":{
  "categorical_question": "int"
  "scale_question": "int"
  }
}

  
Пример обработки (твоя внутренняя логика)
1.  Получив "summary" по каждому объекту, нужно объединить их и сделать общие выводы по всему опросу.
Выбрать наиболее важные факты и написать общее summary (4-5 предложений)
2. Получив темы "themes" каждого объекта, нужно  объединить и отобрать из полученных 10 наиболее важных тем.
Для каждой темы подсчитать новое число ответов, которые вошли в тему. Каждая тема должна также содержать 3 отобранные цитаты из ответов участников.
3. Получив инсайты "insights", нужно объединить их и отобрать 4 наиболее важных. Также нужно сделать с рекомендациями "recommendations", отобрать 4 рекомендации. 
При этом учесть поля уровня важности, цвета и эмодзи.
4. Получив два ключевых вопроса по каждому объекту, нужно выбрать два наиболее часто встречающихся.

Схема ответа (JSON Schema)
Сгенерируй JSON строго по той же схеме, что имеют JSON-объекты (была указана выше).

Справочник цветов и Emoji для фронтенда
Используй исключительно следующие значения:

Для инсайтов (insights):
- positive: тип "positive", emoji "✅", цвет "#059669"
- warning: тип "warning", emoji "⚠️", цвет "#D97706"
- critical: тип "critical", emoji "🔴", цвет "#DC2626"
- neutral: тип "neutral", emoji "ℹ️", цвет "#4B5563"

Для рекомендаций (recommendations: priority_color):
- high: цвет "#DC2626"
- medium: цвет "#D97706"
- low: цвет "#059669"

Итоговое действие
Сгенерируй итоговый JSON. Проверь его валидность и соответствие всем пунктам перед выводом.
"""

# ─── Эндпоинт генерации ИИ-аналитики опроса ───
@router.post(
    "/ai_analytics",
    status_code=status.HTTP_200_OK,
    summary="Сгенерировать аналитику с помощью AI",
    description="Вызывает LLM по промпту и возвращает аналитический отчёт по результатам опроса."
)
async def generate_analytics(
        req: PollResultsResponse,
        current_user: User = Depends(get_current_user()),
        llm_service: ApiLLMService = Depends(get_llm_service),
        db: AsyncSession = Depends(get_assync_db)):
    answers_list, poll_title, poll_description, poll_type, poll_language  = await get_text_answers(req.id, current_user.id, db)
    try: 
        # Валидация входных данных
        if not answers_list:
            logger.warning("Нет текстовых ответов для анализа")
            return {
                "status": "no_data",
                "message": "Нет текстовых ответов для анализа",
                "analytics": {}
            }
    
        batch_size = 100
        
        # Создаем батчи с весами
        batches = []
        for i in range(0, len(answers_list), batch_size):
            batch = answers_list[i:i+batch_size]
            weight = len(batch) / batch_size  # вес = количество ответов в батче / 10
            batches.append({
                'answers': batch,
                'weight': weight,
                'batch_num': i // batch_size + 1
            })
        
        # Если нет текстовых ответов, создаем один пустой батч
        if not batches:
            batches.append({
                'answers': [],
                'weight': 0,
                'batch_num': 1
            })
        
        logger.info(f"Разбито на {len(batches)} батчей. Веса: {[b['weight'] for b in batches]}")
        
        # 2. Функция для обработки одного батча
        async def process_batch(batch_data: dict, system_prompt: str) -> dict:
            start_time = time.time()
            logger.info(f"Батч {batch_data['batch_num']} начал выполнение в {start_time}")

            batch_answers = '\n'.join(batch_data['answers']) if batch_data['answers'] else "Нет ответов в этом батче"
            
            poll_params = (
                f"Название: {poll_title}. "
                f"Описание: {poll_description}. "
                f"Язык: {poll_language}. Тип опроса: {poll_type}. "
                f"Результаты опроса: {req}"
                f"Текстовые ответы: {batch_answers}"
            )
            
            llm_params = LLMRequestParams(
                prompt=poll_params,
                model=DEFAULT_MODEL,
                temperature=0.1,
                max_tokens=32000,
                top_p=0.9,
                response_format={"type": "json_object"}
            )
            
            try:
                llm_data = await llm_service.generate_ai(llm_params, system_prompt, timeout=600)
                
                # Добавляем метаинформацию о батче
                if isinstance(llm_data, dict):
                    llm_data['_batch_metadata'] = {
                        'batch_num': batch_data['batch_num'],
                        'weight': batch_data['weight'],
                        'answers_count': len(batch_data['answers'])
                    }
                logger.info(f"Батч {batch_data['batch_num']} закончил за {time.time() - start_time} сек")
                return llm_data
            except Exception as e:
                logger.error(f"Ошибка в батче {batch_data['batch_num']}: {str(e)}")
                # Возвращаем fallback для ошибочного батча
                return {
                    "error": f"Ошибка обработки батча {batch_data['batch_num']}",
                    "_batch_metadata": {
                        'batch_num': batch_data['batch_num'],
                        'weight': batch_data['weight'],
                        'error': str(e)
                    }
                }
            
        system_prompt = SYSTEM_PROPMT_ANALYTICS + START_PROMPT_ANALYTICS
        # 3. Запуск батчей 
        if len(batches) == 1:
            # Для одного батча - выполняем напрямую, без asyncio.gather
            logger.info("Один батч")
            generate_results = [await process_batch(batches[0],system_prompt)]
        else:
            # Для нескольких батчей
            logger.info(f"{len(batches)} батчей")
            tasks = [process_batch(batch, system_prompt) for batch in batches]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            summary_prompt = SYSTEM_PROPMT_ANALYTICS + SUMMARY_PROMPT_ANALYTICS
            
            generate_results = await process_batch(batch_results, summary_prompt, timeout=600)

         # ─── АГРЕГАЦИЯ SENTIMENT, THEMES, INSIGHTS, RECOMMENDATIONS ИЗ BATCH_RESULTS ───
        total_counts = {"positive": 0, "neutral": 0, "negative": 0}
        aggregated_themes = {}
        aggregated_insights = []
        aggregated_recommendations = []
        summary_parts = []
        key_questions = None

        for result in generate_results:
            if isinstance(result, dict):
                # Агрегация sentiment
                if "sentiment" in result:
                    sentiment = result["sentiment"]
                    total_counts["positive"] += sentiment.get("positive", {}).get("count", 0) if isinstance(sentiment.get("positive"), dict) else sentiment.get("positive", 0)
                    total_counts["neutral"] += sentiment.get("neutral", {}).get("count", 0) if isinstance(sentiment.get("neutral"), dict) else sentiment.get("neutral", 0)
                    total_counts["negative"] += sentiment.get("negative", {}).get("count", 0) if isinstance(sentiment.get("negative"), dict) else sentiment.get("negative", 0)
                
                # Агрегация themes
                if "themes" in result and isinstance(result["themes"], list):
                    for theme in result["themes"]:
                        theme_name = theme.get("theme")
                        if theme_name:
                            if theme_name not in aggregated_themes:
                                aggregated_themes[theme_name] = {"count": 0, "quotes": []}
                            aggregated_themes[theme_name]["count"] += theme.get("count", 0)
                            aggregated_themes[theme_name]["quotes"].extend(theme.get("quotes", [])[:2])
                
                # Сбор insights и recommendations
                if "insights" in result and isinstance(result["insights"], list):
                    aggregated_insights.extend(result["insights"])
                
                if "recommendations" in result and isinstance(result["recommendations"], list):
                    aggregated_recommendations.extend(result["recommendations"])
                
                # Сбор summary и key_questions
                if "summary" in result:
                    summary_parts.append(result["summary"])
                
                if "key_questions" in result and key_questions is None:
                    key_questions = result["key_questions"]

        # Формирование итогового словаря
        total_responses = sum(total_counts.values())
        negative_percentage = round((total_counts["negative"] / total_responses * 100), 2) if total_responses > 0 else 0

        aggregated_result = {
            "summary": " ".join(summary_parts) if summary_parts else "Аналитика сгенерирована",
            "sentiment": {
                "positive": {"count": total_counts["positive"], "percentage": round((total_counts["positive"] / total_responses * 100), 2) if total_responses > 0 else 0},
                "neutral": {"count": total_counts["neutral"], "percentage": round((total_counts["neutral"] / total_responses * 100), 2) if total_responses > 0 else 0},
                "negative": {"count": total_counts["negative"], "percentage": negative_percentage},
                "conclusion": f"{negative_percentage}% текстовых ответов имеют негативную тональность, что указывает на {'критическую' if negative_percentage >= 60 else 'значительную' if negative_percentage >= 40 else 'умеренную'} неудовлетворенность сотрудников." if total_responses > 0 else "Нет данных"
            },
            "themes": [{"theme": name, "count": data["count"], "quotes": data["quotes"]} for name, data in aggregated_themes.items()],
            "insights": aggregated_insights,
            "recommendations": aggregated_recommendations,
            "aggregated_values": await get_aggregate_val(req.id, current_user.id, db, key_questions.get("categorical_question"), key_questions.get("scale_question")) if key_questions else {},
        }
        logger.info(f"AI аналитика для опроса {req.id} сгенерирована")
        
        try:
            analytics_response = AnalyticsResponse(**aggregated_result)
        except ValidationError as e:
            logger.error(f"Ошибка валидации аналитики: {e.errors()}")
            raise HTTPException(status_code=422, detail=f"Ошибка структуры аналитики: {e.errors()}")

        # Сохраняем AI-резюме
        summary_text = json.dumps(aggregated_result, ensure_ascii=False, default=str)
        ai_summary = AiSummary(
            poll_id=req.id,
            summary_text=summary_text
        )
        db.add(ai_summary)
        
        # Сохраняем AI-запрос
        ai_request = AiRequest(
            user_id=current_user.id,
            poll_id=req.id,
            request_type='summary'
        )
        db.add(ai_request)
        
        # Коммитим изменения
        await db.commit()
        logger.info(f"AI аналитика для опроса {req.id} сохранена в БД. Summary ID: {ai_summary.id}, Request ID: {ai_request.id}")
        return analytics_response
    
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
