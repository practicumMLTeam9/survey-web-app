from passlib.context import CryptContext    # зеркало: pip install -i https://mirrors.cloud.tencent.com/pypi/simple passlib[bcrypt]
from jose import JWTError, jwt              # pip install -i https://mirrors.cloud.tencent.com/pypi/simple python-jose
from typing import Optional
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.security.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS
import secrets
import hashlib

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

security_scheme = HTTPBearer(auto_error=False)

def hash_password(password):
    """Хеширование пароля"""
    # bcrypt работает с байтами, поэтому кодируем в UTF-8
    if len(password.encode('utf-8')) > 72:
        # Обрезаем до 72 байт
        password = password.encode('utf-8')[:72].decode('utf-8', errors='ignore')
    return pwd_context.hash(password)


def verify_password(original_password, hashed_password):
    """Проверка пароля"""
    return pwd_context.verify(original_password, hashed_password)


def create_access_token(user_data: dict, expires_delta: Optional[timedelta] = None):
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    user_data.update({"exp": expire, "type": "access"})
    return jwt.encode(user_data, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_data: dict):
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    user_data.update({"exp": expire, "type": "refresh"})
    return jwt.encode(user_data, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str):
    """Расшифровка токена"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
    

async def get_token(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)):
    """Извлекает токен из заголовка Authorization: Bearer ..."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен не предоставлен",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials


def get_current_user(db: dict[str, dict], token_type: str = "access"):
    """Валидация access/refresh токенов.
        Принимает соединение с БД, тип токена и сам токен из заголовка запроса.
        Возвращает данные пользователя из БД
    """
    async def dependency(access_token: str = Depends(get_token)):
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный или просроченный токен"
        )
        payload = decode_token(access_token)
        if payload is None or payload.get("type") != token_type:
            raise credentials_exception

        sub_email = payload.get("sub")
        if sub_email is None:
            raise credentials_exception
        
        user = db.get(sub_email)
        if user is None:
            raise credentials_exception
        return user
    return dependency


def hash_token(token):
    """Хеширование токена"""
    return hashlib.sha256(token.encode()).hexdigest()


def create_reset_token():
    """Генерация одноразового токена для восстановления пароля"""
    reset_token = secrets.token_urlsafe(32)
    reset_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    token_hash = hash_token(reset_token)
    return {
        "token": reset_token,      
        "token_hash": token_hash,  
        "expires_at": reset_expires_at
    }