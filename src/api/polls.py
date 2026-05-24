from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status, HTTPException, Body, Path
from sqlalchemy.ext.asyncio import AsyncSession

from src.api_schemas.poll import PollCreate, PollCreatedResponse, PollSummary, PollDetailResponse, PollResultsResponse, \
    VoteResponse, VoteRequest, PollStatusUpdate
from src.db.async_session import get_db as get_assync_db
from src.db.models import User
from src.security.security import get_current_user, get_respondent_token, security_scheme
from src.services.poll_service import create_poll_service, get_poll_with_details, vote_poll_service, get_list_polls, \
    get_poll_results, start_vote_service
from src.utils.external_urls import get_frontend_vote_url

router = APIRouter(
    prefix="/api/v1/polls",
    tags=["Polls"],
    dependencies=[Depends(security_scheme)],  # ← глобальная проверка для всех методов в роутере
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
        current_user: User = Depends(get_current_user()),
        db: AsyncSession = Depends(get_assync_db)):
    """
    Создает опрос от имени аутентифицированного пользователя.
    """
    user_id = current_user.id
    poll_id = await create_poll_service(db=db, poll_in=poll_in, user_id=user_id)
    external_vote_link = get_frontend_vote_url(poll_id)

    return PollCreatedResponse(id=poll_id,
                               title=poll_in.title,
                               vote_link=external_vote_link,
                               status=poll_in.status)


@router.get("/",
            response_model=list[PollSummary],
            summary="Получить список опросов пользователя",
            description="Возвращает список опросов пользователя, отсортированный по дате создания опроса(сначала последние)",
            tags=["Polls"])
async def list_polls(
        current_user: User = Depends(get_current_user()),
        db: AsyncSession = Depends(get_assync_db)):

    user_id = current_user.id
    return await get_list_polls(db=db, user_id=user_id)



@router.get("/{poll_id}",
            response_model=PollDetailResponse,
            summary="Получить детали опроса",
            description="Возвращает полную структуру опроса с вопросами и вариантами, отсортированными по порядку.")
async def get_poll(poll_id: int = Path(..., ge=1, description="Уникальный идентификатор опроса"),
                   db: AsyncSession = Depends(get_assync_db)):
    poll = await get_poll_with_details(db, poll_id)
    if not poll:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Опрос не найден"
        )
    # if poll.status == "draft":
    #     raise HTTPException(status_code=403, detail="Доступ к черновику ограничен")
    #
    return poll


@router.get("/{poll_id}/results",
            response_model=PollResultsResponse,
            summary="Получить результаты опроса",
            description="Возвращает агрегированные результаты голосования с процентами.",
            tags=["Results"])
async def get_results(poll_id: int, 
                           current_user: dict = Depends(get_current_user()), 
                           db: AsyncSession = Depends(get_assync_db)):
    user_id = current_user.id
    results_data = await get_poll_results(poll_id, user_id, db)
    return results_data


@router.post("/{poll_id}/vote",
             response_model=VoteResponse,
             status_code=status.HTTP_200_OK,
             summary="Проголосовать в опросе",
             description="Принимает выбранный вариант и создаёт новый голос в таблице Answers.",
             tags=["Voting"])
async def vote_poll(poll_id: int, 
                    vote: VoteRequest, 
                    request: Request, 
                    response: Response,
                    db: AsyncSession = Depends(get_assync_db)):
    """Проголосовать в опросе"""
    respondent_token = get_respondent_token(request, response)
    async with db.begin():
        answers = await vote_poll_service(poll_id, vote, respondent_token, db)
    return VoteResponse(
        poll_id=poll_id, answers_confirmed=answers, message="Голос успешно учтён"
    )


@router.post("/{poll_id}/vote/start",
             status_code=status.HTTP_200_OK,
             summary="Начать прохождение опроса",
             description="Сохраняет факт начала прохождения опроса. Создаёт запись в таблице Submissions с временем начала и respondent_token",
             tags=["Voting"])
async def start_vote(poll_id: int, 
                    request: Request, 
                    response: Response,
                    db: AsyncSession = Depends(get_assync_db)):
    """Начать прохождение опроса"""
    respondent_token = get_respondent_token(request, response)
    start_result = await start_vote_service(poll_id, respondent_token, db)
    return start_result


@router.patch(
    "/{poll_id}/status",
    response_model=PollSummary,
    summary="Обновить статус опроса",
    description="Изменяет статус опроса (draft → active → closed). Доступно только создателю.",
    tags=["Polls"]
)
async def update_poll_status(
    poll_id: int = Path(..., ge=1, description="Уникальный идентификатор опроса"),
    status_in: PollStatusUpdate = Body(..., description="Новый статус"),
    current_user: User = Depends(get_current_user()),
    db: AsyncSession = Depends(get_assync_db)
):
    user_id = current_user.id
    return await update_poll_status(db, poll_id, user_id, status_in)

