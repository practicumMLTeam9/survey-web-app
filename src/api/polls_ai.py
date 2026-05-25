import os
import json
import logging
from datetime import datetime
from typing import Dict
from zoneinfo import ZoneInfo

from fastapi import APIRouter, HTTPException, Depends, status, Body
from pydantic import ValidationError

from src.api_schemas.poll import PollCreate, GeneratePollRequest, PollResultsResponse, GenerateAnalyticsRequest
from src.api_schemas.ai import LLMRequestParams, Test
from src.db.models import User
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

  Валидация тем и цитат: Ты должен выделить ровно 10 ключевых тем из открытых ответов. 
Для каждой темы приведи ровно 3 цитаты. Цитаты должны быть дословными выдержками из `answers_list`.
  "themes": [
    {
      "theme": "string (название темы, 2-4 слова)",
      "count": "int (число упоминаний темы)",
      "quotes": ["string", "string", "string"] // ровно 3 цитаты
    }
    // ... всего должно быть 3 элемента(тем)
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
Схема ответа (JSON Schema)
Сгенерируй JSON строго по следующей схеме:
{
  "summary": "string (4-5 предложений с основными выводами)",

  Валидация тем и цитат: Ты должен выделить ровно 10 ключевых тем из открытых ответов. 
Для каждой темы приведи ровно 3 цитаты. Цитаты должны быть дословными выдержками из `answers_list`.
  "themes": [
    {
      "theme": "string (название темы, 2-4 слова)",
      "count": "int (число упоминаний темы)",
      "quotes": ["string", "string", "string"] // ровно 3 цитаты
    }
    // ... всего должно быть 3 элемента(тем)
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
2.  При выделении 10 тем из `answers_list` сгруппируй семантически близкие ответы. 
Если уникальных ответов меньше 10, создай оставшиеся темы с заглушкой "Прочие аспекты", но с пустыми цитатами. Стремись к тому, чтобы значимые темы были первыми.
3.  Формируя `insights`, базируйся на цифрах (корреляция между данными из `votes`, `avg_values`, `sentiment`). 
Не пиши общих фраз типа "Результаты опроса показали...", пиши конкретно: "82% респондентов негативно оценивают скорость работы, что является критическим сигналом".

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
        async def process_batch(batch_data: dict) -> dict:
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
            
            system_prompt = SYSTEM_PROPMT_ANALYTICS + START_PROMPT_ANALYTICS
            
            try:
                llm_data = await llm_service.generate_ai(llm_params, system_prompt)
                
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
        
        # 3. Запуск батчей 
        if len(batches) == 1:
            # Для одного батча - выполняем напрямую, без asyncio.gather
            logger.info("Один батч, выполняю синхронно")
            batch_results = [await process_batch(batches[0])]
        else:
            # Для нескольких батчей
            logger.info(f"{len(batches)} батчей, выполняю асинхронно")
            tasks = [process_batch(batch) for batch in batches]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 4. Агрегация результатов
        aggregated_result = {
            "total_batches": len(batches),
            "total_answers": len(answers_list),
            "batch_results": batch_results,
        }


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
        return aggregated_result
    
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