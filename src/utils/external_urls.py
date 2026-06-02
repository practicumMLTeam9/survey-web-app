from src.core.config import settings

def get_external_vote_url(poll_id: int) -> str:
    """Возвращает полную внешнюю ссылку на голосование."""
    base = settings.PUBLIC_API_URL.rstrip("/")
    return f"{base}/api/v1/polls/{poll_id}/vote"

def get_frontend_vote_url(poll_id: int) -> str:
    """Ссылка на веб-страницу голосования (для пользователей)."""
    base = settings.FRONTEND_URL.rstrip("/")  # например, "https://myapp.com"
    return f"{base}/polls/{poll_id}/vote"  # Страница, которая покажет опрос и отправит POST в API