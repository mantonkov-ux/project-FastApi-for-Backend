# app/modules/auth/route.py

"""
Маршруты для регистрации, авторизации и CRUD пользователей.

Используется:
- регистрация нового пользователя
- получение JWT токена
- получение списка пользователей
- просмотр, обновление и удаление пользователя
"""

from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from typing import List, Optional
from datetime import datetime, timedelta, timezone
import jwt  # PyJWT
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.schema import UserCreate, UserUpdate, UserResponse
from app.modules.auth.service import (
    create_user_service,
    read_user_by_login_service,
    read_user_service,
    read_users_service,
    update_user_service,
    delete_user_service
)
from app.utils.security import hash_password, verify_password
from app.config import settings
from app.utils.database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])

# ────────────── JWT ──────────────
SECRET_KEY = settings.AUTH_SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES = settings.AUTH_TOKEN_EXPIRE_MINUTES
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Создаёт JWT токен на основе данных пользователя и времени жизни токена.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    """
    Проверяет JWT токен и возвращает пользователя.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        login: str = payload.get("sub")
        if login is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = await read_user_by_login_service(login, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return user


# ────────────── Регистрация ──────────────
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Регистрация нового пользователя.
    - Пароль хэшируется перед сохранением
    - Флаг администратора по умолчанию False
    """
    user.is_admin = False
    if user.password:
        user.password = hash_password(user.password)

    try:
        created_user = await create_user_service(user, db)
        return created_user
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Пользователь с логином '{user.login}' уже существует"
        )


# ────────────── Авторизация ──────────────
@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """
    Авторизация пользователя и получение JWT токена.
    Вход: username и password
    Выход: access_token и информация о пользователе
    """
    user = await read_user_by_login_service(form_data.username, db)
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.login},
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


# ────────────── CRUD USERS ──────────────

@router.get("/users", response_model=List[UserResponse])
async def get_users(current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """
    Получение списка всех пользователей (только админ)
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return await read_users_service(db)


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user_by_id(user_id: int, current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """
    Получение информации о пользователе по ID.
    - Админ может получить любого пользователя
    - Обычный пользователь может получить только себя
    """
    user_id = int(user_id)

    if not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    user = await read_user_service(user_id, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return user


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user_update: UserUpdate, current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """
    Обновление пользователя
    - Админ может редактировать любого пользователя, включая флаг is_admin
    - Обычный пользователь может редактировать только себя, флаг is_admin нельзя менять
    """
    user_id = int(user_id)

    # Проверка доступа
    if not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Обычный пользователь не может менять is_admin
    if not current_user.is_admin and user_update.is_admin is not None:
        user_update.is_admin = None

    return await update_user_service(user_id, user_update, db)


@router.delete("/users/{user_id}", status_code=200)
async def delete_user(user_id: int, current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """
    Удаление пользователя
    - Админ может удалить любого
    - Обычный пользователь может удалить только себя
    """
    user_id = int(user_id)

    if not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет досутпа")

    db_user = await read_user_service(user_id, db)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Пользователь {user_id} не найден")

    await delete_user_service(user_id, db)
    return {"detail": f"Пользователь {user_id} удален успешно"}

