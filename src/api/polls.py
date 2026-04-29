from fastapi import APIRouter, Depends, Request, status, HTTPException, Body
from sqlalchemy.orm import Session
from src.db.session import get_db
from typing import Annotated
from src.security.security import get_current_user
from src.schemas.poll import PollCreate, PollCreatedResponse, PollSummary, PollDetailResponse, PollResultsResponse, \
    OptionResult, VoteResponse, VoteRequest
from src.services.poll_service import create_poll_service

router = APIRouter(
    prefix="/api/v1/poll",
    tags=["Polls"],
    responses={404: {"description": "Not found"}},
)


@router.post(
    "/",
    response_model=PollCreatedResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новый опрос",
    description="Принимает название и вопросы с вариантами ответов, возвращает ID опроса и ссылку на опрос."
)

async def create_poll(
    poll_in: Annotated[PollCreate, Body(title="PollCreate")],
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Создает опрос от имени аутентифицированного пользователя.
    """
    user_id = current_user["id"]

    poll_id = create_poll_service(db=db, poll_in=poll_in, user_id=user_id)

    vote_link = f"{request.base_url}polls/{poll_id}"

    return PollCreatedResponse(id=poll_id, title=poll_in.title, vote_link=vote_link)


@router.get("/polls",
         response_model=list[PollSummary],
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
