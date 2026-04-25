# app/modules/examples/notes/schema.py

"""
Pydantic-схемы для модуля notes.

Назначение схем:
1. Описание структуры входных и выходных данных
2. Автоматическая валидация данных (до входа в обработчик)
3. Генерация документации OpenAPI (Swagger)
"""

from pydantic import BaseModel, Field, field_validator


class NoteBase(BaseModel):
    """
    Базовая схема заметки.

    Содержит общие поля заметки.
    Используется как родительская схема:
    - для создания заметки (POST)
    - для возврата данных клиенту (GET)
    """

    title: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Заголовок заметки (3–100 символов)"
    )

    content: str = Field(
        ...,
        min_length=5,
        description="Текст заметки (минимум 5 символов)"
    )

    @field_validator("title")
    @classmethod
    def title_not_uppercase(cls, value: str) -> str:
        """
        Кастомная валидация поля title.

        Правило:
        заголовок не может быть полностью в верхнем регистре.

        Валидация выполняется автоматически
        при создании объекта схемы.
        """
        if value.isupper():
            raise ValueError(
                "Заголовок не может быть полностью в верхнем регистре"
            )
        return value


class NoteCreate(NoteBase):
    """
    Схема для создания заметки (POST /notes).

    Клиент передаёт:
    - title
    - content

    Клиент НЕ передаёт:
    - id (он генерируется сервером)
    """
    pass


class NoteUpdate(BaseModel):
    """
    Схема для частичного обновления заметки (PATCH /notes/{id}).

    Все поля опциональные:
    - позволяет обновлять только часть данных
    """

    title: str | None = Field(
        None,
        min_length=3,
        description="Новый заголовок (опционально)"
    )

    content: str | None = Field(
        None,
        min_length=5,
        description="Новый текст заметки (опционально)"
    )


class Note(NoteBase):
    """
    Схема ответа API (response_model).

    Используется в ответах:
    - GET
    - POST
    - PATCH
    - PUT

    Отличие от NoteCreate:
    - содержит id, который формируется сервером
    """

    id: int = Field(
        description="Уникальный идентификатор заметки"
    )
