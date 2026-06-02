from fastapi import APIRouter, status

router = APIRouter(tags=["System"])

@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Проверка доступности сервиса",
    description="Liveness-проба: отвечает мгновенно, если процесс запущен."
)
async def health_check():
    return {"status": "OK", "version": "1.0.0"}