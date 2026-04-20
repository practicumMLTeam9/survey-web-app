from fastapi import FastAPI, status, HTTPException
import uuid
from datetime import datetime, timezone

from statsmodels.graphics.tukeyplot import results

from src.schemas.poll import (
    PollCreate, PollResponse, PollResultsResponse, OptionResult
)

app = FastAPI(
    title="Poll Application",
    version="1.0.0",
)

# Заглушка: здесь будет SQL / NoSQL база данных
polls_db: dict[str, dict] = {}

@app.get("/")
async def root():
    return {"message": "Hello from src/api/app.py!"}

@app.get("/health")
async def health():
    return {"status": "OK"}

@app.post(
    "/polls",
    response_model=PollResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новый опрос",
    description="Принимает название и варианты ответов, возвращает созданный опрос с уникальным ID."
)
# спринт2: добавить поле location(филиал) в заголовках ?
async def create_poll(poll: PollCreate):
    poll_id = str(uuid.uuid4())

    new_poll = PollResponse(
        id=poll_id,
        title=poll.title,
        options=poll.options,
        description=poll.description,
        created_at=datetime.now(timezone.utc),
        votes={option: 0 for option in poll.options}  # Инициализация счётчиков
    )
    # Сохранение в хранилище
    polls_db[poll_id] = new_poll.model_dump()
    return new_poll


@app.get("/polls/{poll_id}/results", response_model=PollResultsResponse)
async def get_poll_results(poll_id: str):
    if poll_id not in polls_db:
        raise HTTPException(status_code=404, detail="Опрос не найден")
    poll_data = polls_db[poll_id]
    votes = poll_data["votes"]
    total_votes = sum(votes.values())

    results = []
    for option, count in votes.items():
        # Защита от ZeroDivisionError, если ещё никто не голосовал
        percentage = (count / total_votes * 100) if total_votes > 0 else 0.0
        results.append(OptionResult(
            option=option,
            votes=count,
            percentage=round(percentage, 2)
        ))
    return PollResultsResponse(
        id=poll_data["id"],
        title=poll_data["title"],
        results=results,
        total_votes=total_votes,
        created_at=poll_data["created_at"]
    )