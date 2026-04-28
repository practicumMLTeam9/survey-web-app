from fastapi import APIRouter, status, HTTPException, Depends, Request, Response, Query
from datetime import datetime, timezone
from src.schemas.auth import (
    UserRegister, UserResponse, UserLogin, AuthToken, AccessToken, RefreshToken, ForgotPasswordRequest, ResetPasswordLink,
    ResetPasswordRequest
)
from src.security.security import (
    hash_password, verify_password, create_access_token, create_refresh_token, get_current_user, create_reset_token,
    hash_token
)

router = APIRouter(
    prefix="/api/v1/auth",  # ✅ Префикс здесь
    tags=["Authorization"],          # ✅ Теги здесь
    responses={404: {"description": "Not found"}},
)

# Заглушка: здесь будет SQL база данных (таблица users)
users_db: dict[str, dict] = {}


@router.post("/register",
          response_model=UserResponse,
          status_code=status.HTTP_201_CREATED,
          summary="Зарегистрироваться в системе",
          description="Создаёт нового пользователя в системе.",
          tags=["Authorization"])
async def register(user: UserRegister):
    if user.password != user.confirmed_password:
        raise HTTPException(status_code=422, detail="Пароли не совпадают")
     
    if user.email in users_db:
        raise HTTPException(status_code=409, detail="Пользователь с таким email уже существует")
    
    hashed_password = hash_password(user.password)
    new_user = {
        "email": user.email,
        "password_hash": hashed_password,
        "created_at": datetime.now(timezone.utc),
    }
    users_db[new_user["email"]] = new_user
    return UserResponse(
        email=new_user["email"], 
        created_at=new_user["created_at"])


@router.post("/login",
          response_model=AuthToken,
          status_code=status.HTTP_200_OK,
          summary="Войти в систему",
          description="Принимает логин и пароль пользователя, возвращает JWT-токены для доступа и обновления(получения нового токена доступа).\n\n " \
          "Параметры:\n\n" \
          "use_cookie = False отправляет токен напрямую во фронт в формате JSON.\n\n " \
          "use_cookie = True сохраняет токен в cookie браузера. Не работает со Swagger",
          tags=["Authorization"])
async def login(user: UserLogin, response: Response, use_cookie: bool = False):
    user_registered = users_db.get(user.email)
    if user_registered is None or not verify_password(user.password, user_registered.get("password_hash")):
        raise HTTPException(status_code=401, detail="Неверный адрес почты или пароль")
    
    access = create_access_token(user_data={"sub": user_registered["email"]})
    refresh = create_refresh_token(user_data={"sub": user_registered["email"]})
    if not use_cookie:
        access_t = AccessToken(access_token=access,user_email=user_registered["email"])
        refresh_t = RefreshToken(refresh_token=refresh,user_email=user_registered["email"])
        return AuthToken(
            access_token=access_t,
            refresh_token=refresh_t
        )
    else:
        response.set_cookie(
            key = "access_token",
            value = access,
            httponly = True,
            samesite = "lax",
            secure = True
        )
        response.set_cookie(
            key = "refresh_token",
            value = refresh,
            httponly = True,
            samesite = "lax",
            secure = True
        )
    return {"message":"Токен загружен в cookie"}


@router.get("/me",
          response_model=UserResponse,
          summary="Вернуть данные пользователя",
          description="Возвращает информацию о зарегестрированном пользователе по токену доступа.",
          tags=["Authorization"])
async def get_me(current_user = Depends(get_current_user(users_db, "access"))):
    return UserResponse(
        email = current_user["email"],
        created_at = current_user["created_at"]
    )
    

@router.post("/refresh",
          response_model=AccessToken,
          status_code=status.HTTP_202_ACCEPTED,
          summary="Обновить токен доступа",
          description="Проверяет токен обновления, возвращает новый токен доступа. Принимает refresh токен",
          tags=["Authorization"])
async def refresh_access_token(current_user = Depends(get_current_user(users_db, "refresh"))):
    access = create_access_token(user_data={"sub": current_user["email"]})
    return AccessToken(
        access_token=access,
        user_email=current_user["email"]
    )


@router.post("/forgot-password",
          response_model=ResetPasswordLink,
          status_code=status.HTTP_202_ACCEPTED,
          summary="Запросить восстановление пароля",
          description="Создание одноразовой ссылки для смены пароля.",
          tags=["Authorization"])
async def forgot_password(request: Request, body: ForgotPasswordRequest):
    # Генерация одноразового токена
    user = users_db.get(body.email)  
    token_data = create_reset_token()
    # Если пользователь существует — сохраняем хеш и время в БД
    if user:
        users_db[body.email]["reset_token_hash"] = token_data["token_hash"]
        users_db[body.email]["reset_token_expires_at"] = token_data["expires_at"]       
    # Формируем ссылку для сброса
    reset_link = f"{request.base_url}/reset-password?token={token_data['token']}" 
    return ResetPasswordLink(link=reset_link)
        

@router.post("/reset-password", 
          status_code=status.HTTP_201_CREATED,
          summary="Сменить пароль",
          description="Проверяет токен восстановления из ссылки, обновляет пароль пользователя.",
          tags=["Authorization"])
async def reset_password(reset_data: ResetPasswordRequest,
    reset_token: str = Query(..., description="Токен восстановления")):
    token_hash = hash_token(reset_token)
    # Поиск пользователя по токену
    user = None
    for u in users_db.values():
        if (u.get("reset_token_hash") == token_hash and 
            u.get("reset_token_expires_at") and
            u["reset_token_expires_at"] > datetime.now(timezone.utc)):
            user = u
            break
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Недействительный или просроченный токен"
        )
    # Обновление пароля
    user["password_hash"] = hash_password(reset_data.new_password)
    users_db[user["email"]]["password_hash"] = user["password_hash"]
    # Инвалидация токена 
    users_db[user["email"]]["reset_token_hash"] = None
    users_db[user["email"]]["reset_token_expires_at"] = None
    return {"message": "Пароль успешно изменён"}


@router.post("/logout",
          summary="Выйти из системы",
          description="Деактивирует токены пользователя. Не работает со Swagger",
          tags=["Authorization"])
async def logout(response: Response):
    # Клиент просто удаляет токены из localStorage/httpOnly cookie
    # Для полноценной инвалидации нужен Redis blacklist
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message": "Успешный выход из системы"}