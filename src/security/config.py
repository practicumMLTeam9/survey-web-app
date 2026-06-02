from dotenv import load_dotenv
import os

load_dotenv()  # Загружает из .env файла

SECRET_KEY: str = os.getenv("SECRET_KEY")    # import secrets; secrets.token_urlsafe(32) -> str
ALGORITHM: str = os.getenv("ALGORITHM")      # Алгоритм шифрования токена
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))   # Минут до истечения Access токена
REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS"))    # Дней до истечения Refresh токена