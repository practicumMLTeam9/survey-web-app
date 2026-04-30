from pydantic import BaseModel, Field, EmailStr, field_validator
from datetime import datetime
from typing import Optional

class UserRegister(BaseModel):
    """Данные для регистрации нового пользователя"""
    email: EmailStr = Field(..., description="E-mail пользователя")
    password: str = Field(..., min_length=6, max_length=30, description="Пароль пользователя")
    confirmed_password: str = Field(..., min_length=6, max_length=30, description="Подтверждённый пароль")
    first_name: Optional[str] = Field(None, description="Имя")
    last_name: Optional[str] = Field(None, description="Фамилия")
    company_name: Optional[str] = Field(None, description="Компания")
    position: Optional[str] = Field(None, description="Должность")
    phone: Optional[str] = Field(None, description="Телефон")
    interface_language: Optional[str] = Field("ru", description="Язык интерфейса")
    avatar_url: Optional[str] = Field(None, description="Ссылка на аватар")

    @field_validator("password")
    @classmethod
    def password_not_null(cls, v: str) -> str:
        """Явная проверка: пароль не None и не пустая строка"""
        if not v or not v.strip():
            raise ValueError("Пароль не может быть пустым")
        if len(v.strip()) < 6:
            raise ValueError("Пароль должен содержать минимум 6 символов")
        if len(v) > 30:
            raise ValueError("Пароль не длиннее 30 символов")
        return v

class UserLogin(BaseModel):
    """Данные для входа"""
    email: str = Field(..., description="E-mail пользователя")
    password: str = Field(..., min_length=6, max_length=30, description="Пароль")

class UserResponse(BaseModel):
    """Информация о текущем пользователе"""
    email: EmailStr = Field(..., description="E-mail пользователя")
    created_at: datetime = Field(..., description="Время регистрации пользователя")
    id: Optional[int] = Field(..., description="ID пользователя")
    first_name: Optional[str] = Field(None, description="Имя")
    last_name: Optional[str] = Field(None, description="Фамилия")
    company_name: Optional[str] = Field(None, description="Компания")
    position: Optional[str] = Field(None, description="Должность")
    phone: Optional[str] = Field(None, description="Телефон")
    avatar_url: Optional[str] = Field(None, description="Ссылка на аватар")
    interface_language: Optional[str] = Field("ru", description="Язык интерфейса")
    role: Optional[str]

    class Config:
        from_attributes = True 

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