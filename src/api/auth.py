from fastapi import APIRouter, status, HTTPException, Depends, Request, Response, Query
from datetime import datetime, timezone
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession as Session
from src.db.async_session import get_db
from src.db.models import User
from src.api_schemas.auth import (
    UserRegister, UserResponse, UserLogin, AuthToken, AccessToken, RefreshToken, ForgotPasswordRequest, ResetPasswordLink,
    ResetPasswordRequest, UserChangedData, ChangedPassword
)
from src.security.security import (
    hash_password, verify_password, create_access_token, create_refresh_token, get_current_user, create_reset_token,
    hash_token, set_cookies
)

router = APIRouter(
    prefix="/api/v1/auth",  # ✅ Префикс здесь
    tags=["Authorization"],          # ✅ Теги здесь
    responses={404: {"description": "Not found"}},
)


@router.post("/register",
          response_model=UserResponse,
          status_code=status.HTTP_201_CREATED,
          summary="Зарегистрироваться в системе",
          description="Создаёт нового пользователя в системе.",
          tags=["Authorization"])
async def register(user: UserRegister, db: Session = Depends(get_db)):
    if user.password != user.confirmed_password:
        raise HTTPException(status_code=422, detail="Пароли не совпадают")
    
    hashed_password = hash_password(user.password)
    new_user = User(
        email=user.email,
        password_hash=hashed_password,
        first_name=user.first_name,
        last_name=user.last_name,
        company_name=user.company_name,
        position=user.position,
        phone=user.phone,
        interface_language=user.interface_language,
        avatar_url=user.avatar_url,
    )
    db.add(new_user)

    try:
        await db.commit()   # сохраняем в БД
        await db.refresh(new_user)  # получаем id, created_at из БД
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Пользователь с таким email уже существует"
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при регистрации пользователя: {str(e)}"     # str(e) для отлдаки
        )
    return UserResponse.model_validate(new_user)


@router.post("/login",
          status_code=status.HTTP_200_OK,
          summary="Войти в систему",
          description="Принимает логин и пароль пользователя, возвращает JWT-токены для доступа и обновления(получения нового токена доступа).\n\n " \
          "Параметры:\n\n" \
          "use_cookie = False отправляет токен напрямую во фронт в формате JSON.\n\n " \
          "use_cookie = True сохраняет токен в cookie браузера. Не работает со Swagger",
          tags=["Authorization"])
async def login(user: UserLogin, response: Response, db: Session = Depends(get_db), use_cookie: bool = True):
    result = await db.execute(select(User).where(User.email == user.email))
    user_registered = result.scalar_one_or_none()
    if user_registered is None or not verify_password(user.password, user_registered.password_hash):
        raise HTTPException(status_code=401, detail="Неверный адрес почты или пароль")
    
    access = create_access_token(user_data={"sub": user_registered.email})
    refresh = create_refresh_token(user_data={"sub": user_registered.email})
    if not use_cookie:
        access_t = AccessToken(access_token=access,user_email=user_registered.email)
        refresh_t = RefreshToken(refresh_token=refresh,user_email=user_registered.email)
        return AuthToken(
            access_token=access_t,
            refresh_token=refresh_t
        )
    else:
        set_cookies(response, access, refresh)
        return {"message":"Токен загружен в cookie"}


@router.get("/me",
          response_model=UserResponse,
          summary="Вернуть данные пользователя",
          description="Возвращает информацию о зарегестрированном пользователе по токену доступа.",
          tags=["Authorization"])
async def get_me(current_user = Depends(get_current_user())):
    return UserResponse.model_validate(current_user)
    

@router.post("/refresh",
          status_code=status.HTTP_202_ACCEPTED,
          summary="Обновить токен доступа",
          description="Проверяет токен обновления, возвращает новый токен доступа. Принимает refresh токен",
          tags=["Authorization"])
async def refresh_access_token(response: Response, current_user = Depends(get_current_user(token_type = "refresh")),
                               use_cookie: bool = True):
    access = create_access_token(user_data={"sub": current_user.email})
    if not use_cookie:
        return AccessToken(
        access_token=access,
        user_email=current_user.email
    )
    else:
        response.set_cookie(
            key = "access_token",
            value = access,
            httponly = True,
            samesite = "lax",
            secure = True
        )
        return {"message":"Токен загружен в cookie"}


@router.post("/forgot-password",
          response_model=ResetPasswordLink,
          status_code=status.HTTP_202_ACCEPTED,
          summary="Запросить восстановление пароля",
          description="Создание одноразовой ссылки для смены пароля.",
          tags=["Authorization"])
async def forgot_password(request: Request, body: ForgotPasswordRequest, db: Session = Depends(get_db)):
    # Генерация одноразового токена
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    token_data = create_reset_token()
    # Если пользователь существует — сохраняем хеш и время в БД
    if user:
        user.reset_token_hash = token_data["token_hash"]
        user.reset_token_expires_at = token_data["expires_at"]
        try:
            await db.commit()
        except Exception:
            await db.rollback()  
    # Формируем ссылку для сброса
    reset_link = f"{request.base_url}/reset-password?token={token_data['token']}" 
    return ResetPasswordLink(link=reset_link)
        

@router.post("/reset-password", 
          status_code=status.HTTP_201_CREATED,
          summary="Сменить пароль",
          description="Проверяет токен восстановления из ссылки, обновляет пароль пользователя.",
          tags=["Authorization"])
async def reset_password(reset_data: ResetPasswordRequest,
    reset_token: str = Query(..., description="Токен восстановления"), db: Session = Depends(get_db)):
    token_hash = hash_token(reset_token)
    # Поиск пользователя по токену
    now_utc = datetime.now(timezone.utc)
    result = await db.execute(
        select(User).where(
            (User.reset_token_hash == token_hash) &
            (User.reset_token_expires_at.isnot(None)) &
            (User.reset_token_expires_at > now_utc)
        )
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Недействительный или просроченный токен"
        )
    # Обновление пароля
    new_password_hash = hash_password(reset_data.new_password)
    user.password_hash = new_password_hash
    # Инвалидация токена 
    user.reset_token_hash = None
    user.reset_token_expires_at = None
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при сохранении нового пароля"
        )
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


@router.patch("/update-profile",
          response_model=UserResponse,
          summary="Изменить данные пользователя",
          description="Сохраняет изменённые данные зарегестрированного пользователя.",
          tags=["Authorization"])
async def update_profile(changed_data: UserChangedData, 
                         current_user = Depends(get_current_user()),
                         db: Session = Depends(get_db)):   
    
    update_data = {}
    if changed_data.email is not None:
        update_data["email"] = changed_data.email
    if changed_data.first_name is not None:
        update_data["first_name"] = changed_data.first_name
    if changed_data.last_name is not None:
        update_data["last_name"] = changed_data.last_name
    if changed_data.company_name is not None:
        update_data["company_name"] = changed_data.company_name
    if changed_data.position is not None:
        update_data["position"] = changed_data.position
    if changed_data.phone is not None:
        update_data["phone"] = changed_data.phone
    if changed_data.interface_language is not None:
        update_data["interface_language"] = changed_data.interface_language
    if changed_data.avatar_url is not None:
        update_data["avatar_url"] = changed_data.avatar_url
    
    if not update_data:
        # Ничего не обновляем, возвращаем пользователя
        return await db.get(User, current_user.id)
    try:
        result = await db.execute(
            update(User)
            .where(User.id == current_user.id)
            .values(**update_data)
            .returning(User)
        )
        await db.commit()
        
        user = result.scalar_one_or_none()
        return user
        
    except Exception:
        await db.rollback()
        raise


@router.patch("/change-password",
          summary="Изменить пароль пользователя",
          description="Сохраняет новый пароль зарегестрированного пользователя.",
          tags=["Authorization"])
async def change_password(new_password: ChangedPassword, current_user = Depends(get_current_user()),
                          db: Session = Depends(get_db)):
    if new_password.password != new_password.confirmed_password:
        raise HTTPException(status_code=422, detail="Пароли не совпадают")
    
    hashed_password = hash_password(new_password.password)
    try:
        result = await db.execute(
            update(User)
            .where(User.id == current_user.id)
            .values(password_hash=hashed_password)
            .returning(User.id)
        )
        await db.commit()
        
        # Проверяем, был ли обновлён хотя бы один ряд
        updated_id = result.scalar_one_or_none()
        return updated_id is not None
        
    except Exception:
        await db.rollback()
        raise