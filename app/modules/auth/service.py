# app/modules/auth/service.py

"""
Сервисный слой для работы с пользователями (User).

Назначение:
1. Отделение бизнес-логики от маршрутов (routes)
2. Работа с базой данных через SQLAlchemy AsyncSession
3. CRUD операции:
    - создание пользователя
    - чтение пользователей
    - обновление пользователя
    - удаление пользователя
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError

from app.modules.auth.model import User
from app.modules.auth.schema import UserCreate, UserUpdate

# ────────────── CREATE ──────────────
async def create_user_service(user_data: UserCreate, db: AsyncSession) -> User:
    """
    Создаёт нового пользователя в базе данных.
    - Пароль должен быть уже захэширован
    - Проверяет уникальность логина через БД (IntegrityError)
    """
    db_user = User(
        login=user_data.login,
        name=user_data.name,
        password=user_data.password,
        is_admin=user_data.is_admin
    )
    db.add(db_user)
    try:
        await db.commit()
        await db.refresh(db_user)  # Получаем данные после вставки
    except IntegrityError as e:
        await db.rollback()
        raise e
    return db_user


# ────────────── READ ──────────────
async def read_users_service(db: AsyncSession) -> list[User]:
    """
    Возвращает список всех пользователей из базы данных.
    Используется для админских операций.
    """
    result = await db.execute(select(User))
    return result.scalars().all()


async def read_user_service(user_id: int, db: AsyncSession) -> User | None:
    """
    Возвращает одного пользователя по ID.
    Если пользователь не найден, возвращает None.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def read_user_by_login_service(login: str, db: AsyncSession) -> User | None:
    """
    Возвращает одного пользователя по логину.
    Используется при авторизации.
    """
    result = await db.execute(select(User).where(User.login == login))
    return result.scalar_one_or_none()


# ────────────── UPDATE ──────────────
async def update_user_service(user_id: int, user_update: UserUpdate, db: AsyncSession) -> User:
    """
    Обновляет данные пользователя.
    - Пароль должен быть уже захэширован
    - Проверяет уникальность логина через БД
    """
    db_user = await read_user_service(user_id, db)
    if not db_user:
        return None

    for key, value in user_update.dict(exclude_unset=True).items():
        setattr(db_user, key, value)

    try:
        await db.commit()
        await db.refresh(db_user)
    except IntegrityError as e:
        await db.rollback()
        raise e

    return db_user


# ────────────── DELETE ──────────────
async def delete_user_service(user_id: int, db: AsyncSession) -> None:
    """
    Удаляет пользователя по ID.
    """
    db_user = await read_user_service(user_id, db)
    if not db_user:
        return None

    await db.delete(db_user)
    await db.commit()
