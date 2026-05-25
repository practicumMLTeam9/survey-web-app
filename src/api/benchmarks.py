from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.async_session import get_db as get_assync_db
from src.db.models import AiRequest, Poll

router = APIRouter(prefix="/api/v1/benchmarks", tags=["AI Analytics"])

# Ориентировочные цены за 1K токенов (обновите при подключении платных моделей)
_MODEL_PRICES = {
    "baidu/cobuddy:free": 0.0,
    "google/gemini-2.0-flash-lite:free": 0.0,
    "qwen/qwen-2.5-7b-instruct:free": 0.0,
    "openai/gpt-4o-mini": 0.0006,
}


@router.get("/summary")
async def get_benchmark_summary(db: AsyncSession = Depends(get_assync_db)):
    """
    Возвращает сводные метрики генерации опросов и рекомендацию лучшей модели.
    """
    # 1. Загрузка сырых данных
    stmt = select(AiRequest, Poll.published_at).outerjoin(
        Poll, AiRequest.poll_id == Poll.id
    ).where(AiRequest.request_type == "generate_poll")
    result = await db.execute(stmt)
    rows = result.all()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail="Нет данных для бенчмарка. Сгенерируйте хотя бы один опрос через AI.")

    # 2. Базовая агрегация
    total = len(rows)
    valid_json = sum(1 for r, _ in rows if r.is_valid_json)
    valid_schema = sum(1 for r, _ in rows if r.is_valid_schema)
    errors = sum(1 for r, _ in rows if r.error_type is not None)
    latencies = sorted([r.latency_ms for r, _ in rows if r.latency_ms is not None])
    tokens = sum(r.estimated_tokens or 0 for r, _ in rows)
    drafts_created = sum(1 for r, _ in rows if r.poll_id is not None)
    accepted_without_edit = sum(
        1 for r, _ in rows if r.poll_id is not None and r.user_edited_draft is False
    )

    p95_latency = latencies[int(len(latencies) * 0.95)] if latencies else 0.0
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

    # 3. Полное время: промпт → публикация
    times_to_publish = []
    for r, pub_at in rows:
        if pub_at and r.created_at:
            times_to_publish.append((pub_at - r.created_at).total_seconds())
    avg_time_to_publish = sum(times_to_publish) / len(times_to_publish) if times_to_publish else 0.0

    # 4. Посчёт метрик по каждой модели
    model_stats = {}
    for r, _ in rows:
        m = r.model or "unknown"
        if m not in model_stats:
            model_stats[m] = {"total": 0, "valid_schema": 0, "accepted": 0, "latencies": [], "tokens": 0}
        model_stats[m]["total"] += 1
        if r.is_valid_schema: model_stats[m]["valid_schema"] += 1
        if r.poll_id is not None and r.user_edited_draft is False:
            model_stats[m]["accepted"] += 1
        if r.latency_ms: model_stats[m]["latencies"].append(r.latency_ms)
        if r.estimated_tokens: model_stats[m]["tokens"] += r.estimated_tokens

    # 5. Выбор лучшей модели (взвешенный скоринг)
    best_model = None
    best_score = -1.0

    for m, data in model_stats.items():
        if data["total"] == 0:
            continue
        schema_rate = data["valid_schema"] / data["total"]
        avg_lat = sum(data["latencies"]) / max(len(data["latencies"]), 1)
        accept_rate = data["accepted"] / max(drafts_created, 1)
        cost = (data["tokens"] / 1000) * _MODEL_PRICES.get(m, 0)

        # Формула: 40% качество + 30% скорость + 20% цена + 10% принятие без правок
        speed_score = max(0.0, 1 - (avg_lat / 5000))      # <5с = 1.0, >5с = 0.0
        cost_score = max(0.0, 1 - (cost * 1000))         # <$0.001 = 1.0
        score = (schema_rate * 0.4) + (speed_score * 0.3) + (cost_score * 0.2) + (accept_rate * 0.1)

        if score > best_score:
            best_score = score
            best_model = {
                "model": m,
                "score": round(score, 3),
                "metrics": {
                    "schema_adherence_rate": round(schema_rate, 3),
                    "avg_latency_ms": round(avg_lat, 1),
                    "acceptance_rate": round(accept_rate, 3),
                    "estimated_cost_per_request_usd": round(cost, 6)
                }
            }

    # 6. Формирование ответа
    return {
        "total_requests": total,
        "metrics": {
            "valid_json_pct": round((valid_json / total) * 100, 1),
            "valid_schema_pct": round((valid_schema / total) * 100, 1),
            "avg_latency_ms": round(avg_latency, 1),
            "p95_latency_ms": round(p95_latency, 1),
            "error_rate_pct": round((errors / total) * 100, 1),
            "draft_acceptance_pct": round((accepted_without_edit / max(drafts_created, 1)) * 100, 1),
            "avg_time_to_publish_sec": round(avg_time_to_publish, 1)
        },
        "recommendation": best_model,
        "scoring_formula": "Score = 0.4*Schema + 0.3*Speed + 0.2*Cost + 0.1*Acceptance"
    }