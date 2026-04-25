# app/modules/gpt_crud/schema.py

"""
Схемы данных для модуля gpt_crud.

Назначение:
1. Входные данные от пользователя (текстовая команда)
2. Выходные данные с SQL-запросом и/или результатом
"""

from pydantic import BaseModel, Field


class GPTCRUDRequest(BaseModel):
    """
    Схема запроса к GPT для генерации SQL.
    
    Пример:
        prompt: "Покажи все заметки пользователя user_test"
    """
    prompt: str = Field(..., description="Команда от пользователя для генерации SQL")


class GPTCRUDResponse(BaseModel):
    """
    Схема ответа от GPT.
    
    Содержит:
    - сгенерированный SQL
    - необязательный результат запроса к базе
    """
    sql: str
    rows: list[dict] | None = None
    message: str | None = None
    