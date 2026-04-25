# app/modules/auth/schema.py

"""
Pydantic-схемы для модуля авторизации.

Назначение схем:
1. Валидация входных данных при регистрации и авторизации.
2. Описание структуры данных для API (response_model).
3. Генерация документации OpenAPI (Swagger).
"""

from pydantic import BaseModel, Field
from datetime import datetime


class UserBase(BaseModel):
    """
    Базовая схема пользователя.
    
    Содержит общие поля:
    - имя пользователя
    - логин
    Используется как родительская схема для создания и ответа API.
    """

    name: str | None = Field(
        None,
        min_length=2,
        max_length=100,
        description="Имя пользователя (опционально)"
    )

    login: str | None = Field(
        None,
        min_length=3,
        max_length=50,
        description="Логин пользователя (уникальный)"
    )


class UserCreate(UserBase):
    """
    Схема для регистрации/создания пользователя.

    Клиент передаёт:
    - login
    - password
    - name (опционально)
    """
    password: str = Field(
        ...,
        min_length=5,
        max_length=128,
        description="Пароль пользователя"
    )

    is_admin: bool = Field(
        default=False,
        description="Флаг администратора (по умолчанию False)"
    )


class UserUpdate(BaseModel):
    """
    Схема для обновления пользователя.

    Все поля опциональные:
    - позволяет обновлять только часть данных
    """
    name: str | None = Field(None, min_length=2, max_length=100)
    login: str | None = Field(None, min_length=3, max_length=50)
    password: str | None = Field(None, min_length=5, max_length=128)
    is_admin: bool | None = None


class UserResponse(UserBase):
    """
    Схема ответа API (response_model) для пользователя.
    
    Содержит id и флаг администратора.
    """
    id: int = Field(..., description="Уникальный идентификатор пользователя")
    is_admin: bool = Field(False, description="Флаг администратора")
    created_at: datetime | None = Field(None, description="Дата и время создания записи")
