from fastapi import APIRouter, status, HTTPException, Request
import uuid
from datetime import datetime, timezone
from src.schemas.poll import (
    PollCreate, PollResponse, PollResultsResponse, OptionResult, PollDetailResponse, PollSummary, VoteResponse,
    VoteRequest, PollCreatedResponse
)
from typing import List

router = APIRouter(
    prefix="/api/v1/polls",  # ✅ Префикс здесь
    tags=["Polls"],          # ✅ Теги здесь
    responses={404: {"description": "Not found"}},
)

# Заглушка
polls_db: dict[str, dict] = {}

@router.get("/", tags=["Root"], summary="Корневой эндпоинт",
         description="Возвращает приветственное сообщение и статус сервиса.")
async def root():
    return {"message": "Hello from src/api/app.py!"}


@router.get("/health", tags=["Health"], summary="Проверка здоровья",
         description="Эндпоинт для проверки доступности сервиса (healthcheck).")
async def health():
    return {"status": "OK"}


@router.post(
    "/polls",
    response_model=PollResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новый опрос",
    description="Принимает название и вопросы с вариантами ответов, возвращает созданный опрос с уникальным ID.",
    tags=["Polls"]
)
# спринт2: добавить поле location(филиал) в заголовках ?
async def create_poll(poll: PollCreate, request: Request,):
    poll_id = str(uuid.uuid4())

    # Инициализируем вопросы со счётчиками голосов
    questions_data = []
    for q in poll.questions:
        questions_data.append({
            "question_text": q.question_text,
            "options": q.options,
            "text_answer": q.text_answer,
            "votes": {opt: 0 for opt in q.options}  # Счётчик для каждого варианта
        })

        # Сохраняем в хранилище
        polls_db[poll_id] = {
            "id": poll_id,
            "title": poll.title,
            "city": poll.city,
            "description": poll.description,
            "created_at": datetime.now(timezone.utc),
            "questions": questions_data
        }
        # Формируем ссылку (относительную или абсолютную)
        vote_link = f"{request.base_url}polls/{poll_id}"

        return PollCreatedResponse(id=poll_id, title=poll.title, vote_link=vote_link)


@router.get("/polls",
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


@router.get("/polls/{poll_id}",
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


@router.get("/polls/{poll_id}/results",
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


@router.post("/polls/{poll_id}/vote",
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
