# app/modules/gpt_crud/service.py

"""
Сервисный слой для GPT CRUD с учётом текущего пользователя.

Назначение:
1. Асинхронное чтение базового промпта из файла base/crud.md при каждом обращении
2. Генерация SQL-запросов на основе команды пользователя с учётом user_id
3. Опциональное выполнение SQL-запроса через SQLAlchemy AsyncSession
4. Поддержка поиска по корням слов через LIKE '%слово%'
5. Обработка SELECT и не-SELECT запросов корректно
6. Логирование всех шагов через app.state.log
"""

import aiofiles
import httpx
import os
from app.config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List, Dict
from fastapi import Request

# ────────────── LLM настройки ──────────────
LLM_BASE_URL = getattr(settings, "LLM_BASE_URL", "https://api.openai.com/v1/responses")
LLM_MODEL = getattr(settings, "LLM_MODEL", "gpt-4o-mini")
LLM_API_KEY = getattr(settings, "LLM_API_KEY", "")

# ────────────── Путь к файлу с базовым промптом ──────────────
CRUD_PROMPT_FILE = "base/crud.md"

# ────────────── Асинхронное чтение промпта ──────────────
async def read_prompt() -> str:
    """
    Асинхронное чтение промпта из файла base/crud.md при каждом вызове.
    Если файл не найден — возвращается дефолтный промпт.
    """
    if os.path.exists(CRUD_PROMPT_FILE):
        async with aiofiles.open(CRUD_PROMPT_FILE, mode="r", encoding="utf-8") as f:
            return await f.read()
    return "You are a SQL generator for notes app. Generate CRUD SQL queries based on user request."


# ────────────── Вызов LLM с user_id ──────────────
async def call_gpt(
    user_request: str,
    user_id: int,
    request: Request,
    temperature: float = 0.7,
    max_tokens: int = 300
) -> str:
    """
    Асинхронный вызов GPT для генерации SQL с учётом user_id.
    Promt читается при каждом вызове.
    Логирование всех шагов через app.state.log
    """
    log = request.app.state.log

    # ────────────── Логируем получение запроса ──────────────
    await log.log_info(target="GPT CRUD", message=f"Получен пользовательский запрос: {user_request}")
    await log.log_info(target="GPT CRUD", message=f"Определён user_id: {user_id}")

    # ────────────── Чтение базового промпта ──────────────
    base_prompt = await read_prompt()
    await log.log_info(target="GPT CRUD", message=f"Прочитан базовый промпт (первые 200 символов): {base_prompt[:200]}")

    # ────────────── Формируем полный промпт для LLM ──────────────
    full_prompt = f"""
{base_prompt}

User ID: {user_id}
User request: {user_request}

Rules:
- Все SQL-запросы должны фильтровать записи по User ID.
- Для поиска используем SQL LIKE %слово% для каждого корня слова из запроса.
- Генерируем SQL только для текущего пользователя.
- CRUD операции: CREATE, READ, UPDATE, DELETE.
- Для UPDATE/DELETE сначала ищем note_id через LIKE-поиск.
- Возвращаем только SQL без объяснений.
"""

    await log.log_info(target="GPT CRUD", message=f"Формирование запроса к LLM с учётом user_id")

    headers = {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": LLM_MODEL,
        "input": full_prompt,
        "temperature": temperature,
        "max_output_tokens": max_tokens
    }

    # ────────────── Отправка запроса к LLM ──────────────
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(LLM_BASE_URL, headers=headers, json=payload)
        if resp.status_code != 200:
            await log.log_error(target="GPT CRUD", message=f"Ошибка LLM API: {resp.status_code}, {resp.text}")
            raise RuntimeError(f"LLM API error: {resp.status_code}, {resp.text}")

        data = resp.json()
        try:
            # структура ответа Responses API
            sql_query = data["output"][0]["content"][0]["text"]
        except (KeyError, IndexError, TypeError):
            await log.log_error(target="GPT CRUD", message=f"Неверный формат ответа LLM: {data}")
            raise RuntimeError(f"Unexpected LLM response format: {data}")

    await log.log_info(target="GPT CRUD", message=f"Сгенерирован SQL-запрос:\n{sql_query}")
    return sql_query.strip()


async def execute_sql(sql: str, db: AsyncSession, request: Request) -> dict:
    """
    Выполнение SQL-запроса через SQLAlchemy AsyncSession.
    
    Возвращает:
    - SELECT: sql, title, description, rows
    - INSERT/UPDATE/DELETE: sql, message
    """

    log = request.app.state.log

    # Логируем оригинальный SQL от GPT
    await log.log_info(target="GPT CRUD", message=f"SQL от GPT (raw): {sql}")

    # 1. Убираем Markdown и лишние переносы
    cleaned_sql = (
        sql
        .replace("```sql", "")
        .replace("```", "")
        .replace("\n", " ")
        .strip()
    )
    cleaned_sql = " ".join(cleaned_sql.split())

    # 2. Берём только первый SQL-запрос (до первого ;)
    if ";" in cleaned_sql:
        first_sql = cleaned_sql.split(";", 1)[0].strip() + ";"
    else:
        first_sql = cleaned_sql

    await log.log_info(target="GPT CRUD", message=f"SQL после очистки: {first_sql}")

    # 3. Определяем тип запроса
    sql_type = first_sql.split()[0].upper()

    try:
        # 4. SELECT
        if sql_type == "SELECT":
            result = await db.execute(text(first_sql))
            rows = result.mappings().all()
            await log.log_info(target="GPT CRUD", message=f"Найдено заметок: {len(rows)}")
            return {
                "sql": first_sql,
                "rows": rows, 
            }

        # 5. INSERT/UPDATE/DELETE
        await db.execute(text(first_sql))
        await db.commit()
        message = {
            "INSERT": "Заметка добавлена",
            "UPDATE": "Заметка обновлена",
            "DELETE": "Заметка удалена"
        }.get(sql_type, "Запрос выполнен")

        await log.log_info(target="GPT CRUD", message=f"{sql_type}: выполнено успешно")
        return {
            "sql": first_sql,
            "message": message
        }

    except Exception as e:
        await db.rollback()
        await log.log_error(target="GPT CRUD", message=f"Ошибка при выполнении SQL: {str(e)}")
        raise
