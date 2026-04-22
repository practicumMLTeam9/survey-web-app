from fastapi import FastAPI, status, HTTPException
import uuid
from datetime import datetime, timezone
from src.schemas.poll import (
    PollCreate, PollResponse, PollResultsResponse, OptionResult, PollDetailResponse, PollSummary, VoteResponse,
    VoteRequest
)
from typing import List

app = FastAPI(
    title="Poll Application",
    version="1.0.0",
)

# Заглушка: здесь будет SQL / NoSQL база данных
polls_db: dict[str, dict] = {}


@app.get("/", tags=["Root"],summary="Корневой эндпоинт", description="Возвращает приветственное сообщение и статус сервиса.")
async def root():
    return {"message": "Hello from src/api/app.py!"}


@app.get("/health", tags=["Health"],summary="Проверка здоровья", description="Эндпоинт для проверки доступности сервиса (healthcheck).")
async def health():
    return {"status": "OK"}


@app.post(
    "/polls",
    response_model=PollResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новый опрос",
    description="Принимает название и варианты ответов, возвращает созданный опрос с уникальным ID.",
    tags=["Polls"]
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


@app.get("/polls",
         response_model=List[PollSummary],
         summary="Получить список опросов",
         description="Возвращает список допустных опросов",
         tags=["Polls"])
async def list_polls():
    if not polls_db:
        return []
    return [
        PollSummary(
            id=p["id"], title=p["title"], created_at=p["created_at"],
            total_votes=sum(p["votes"].values())
        ) for p in polls_db.values()
    ]


@app.get("/polls/{poll_id}",
         response_model=PollDetailResponse,
         summary="Получить детали опроса",
         description="Возвращает полную информацию об опросе, включая текущие результаты и общее число голосов.",
         tags=["Polls"])
async def get_poll_detail(poll_id: str):
    """Получить детальный опрос"""
    if poll_id not in polls_db:
        raise HTTPException(status_code=404, detail="Опрос не найден")
    
    poll_data = polls_db[poll_id]
    votes = poll_data["votes"]
    total_votes = sum(votes.values())

    # Вычисляем results, так как модель PollDetailResponse требует это поле
    # results = []
    # for option, count in votes.items():
    #     percentage = (count / total_votes * 100) if total_votes > 0 else 0.0
    #     results.append(OptionResult(
    #         option=option,
    #         votes=count,
    #         percentage=round(percentage, 2)
    #     ))

    poll_data = polls_db[poll_id]
    return PollDetailResponse(
        id=poll_data["id"],
        title=poll_data["title"],
        description=poll_data["description"],
        options=poll_data["options"],
        created_at=poll_data["created_at"],
        # results=results,
        total_votes=total_votes
    )


@app.get("/polls/{poll_id}/results", 
         response_model=PollResultsResponse,
         summary="Получить результаты опроса",
         description="Возвращает агрегированные результаты голосования с процентами.",
         tags=["Results"])
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


@app.post("/polls/{poll_id}/vote",
          response_model=VoteResponse,
          status_code=status.HTTP_200_OK,
          summary="Проголосовать в опросе",
          description="Принимает выбранный вариант и увеличивает счётчик голосов. Возвращает обновлённое общее число голосов.",
          tags=["Voting"])
async def vote_poll(poll_id: str, vote: VoteRequest):
    """Проголосовать в опросе"""
    if poll_id not in polls_db:
        raise HTTPException(status_code=404, detail="Опрос не найден")

    poll_data = polls_db[poll_id]
    if vote.option not in poll_data["options"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Недопустимый вариант. Доступные: {', '.join(poll_data['options'])}"
        )

    # Обновляем счётчик в памяти
    poll_data["votes"][vote.option] += 1
    total_votes = sum(poll_data["votes"].values())

    return VoteResponse(
        poll_id=poll_id, voted_option=vote.option,
        total_votes=total_votes, message="Голос успешно учтён"
    )