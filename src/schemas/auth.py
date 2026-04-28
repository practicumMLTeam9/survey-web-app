from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional

class UserRegister(BaseModel):
    """Данные для регистрации нового пользователя"""
    email: EmailStr = Field(..., description="E-mail пользователя")
    password: str = Field(..., min_length=6, max_length=30, description="Пароль")
    confirmed_password: str = Field(..., min_length=6, max_length=30, description="Подтверждённый пароль")

class UserLogin(BaseModel):
    """Данные для входа"""
    email: str = Field(..., description="E-mail пользователя")
    password: str = Field(..., min_length=6, max_length=30, description="Пароль")

class UserResponse(BaseModel):
    """Информация о текущем пользователе"""
    email: EmailStr = Field(..., description="E-mail пользователя")
    created_at: datetime

class AccessToken(BaseModel):
    """Ответ с токеном доступа"""
    access_token: str = Field(..., description="JWT токен")
    token_type: str = Field(default="access", description="Тип токена")
    user_email: str = Field(..., description="E-mail владельца токена")

class RefreshToken(BaseModel):
    """Ответ с токеном обновления"""
    refresh_token: str = Field(..., description="JWT токен")
    token_type: str = Field(default="refresh", description="Тип токена")
    user_email: str = Field(..., description="E-mail владельца токена")

class AuthToken(BaseModel):
    """Ответ с токенами"""
    access_token: AccessToken = Field(..., description="Access токен")
    refresh_token: RefreshToken = Field(..., description="Refresh токен")

class ForgotPasswordRequest(BaseModel):
    """Запрос для восстановления пароля"""
    email: EmailStr = Field(..., description="E-mail пользователя")

class ResetPasswordLink(BaseModel):
    """Ответ со ссылкой для сброса пароля"""
    link: Optional[str] = Field(..., description="Ссылка для восстановления пароля")

class ResetPasswordRequest(BaseModel):
    """Запрос с отправкой нового пароля"""
    new_password: str = Field(..., min_length=6, max_length=30, description="Новый пароль")