"""
Сервисный слой для GPT CRUD с учётом текущего пользователя.
Требования Pro-уровня:
- Работа с полем created_at в заметках
- Передача текущей даты в промпт
- Генерация SQL с фильтрами по временным интервалам
"""

import aiofiles
import httpx
import os
import re
import uuid
import traceback
from app.config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Dict
from fastapi import Request
from datetime import datetime

# ────────────── LLM настройки ──────────────
LLM_BASE_URL = getattr(settings, "LLM_BASE_URL", "https://gigachat.devices.sberbank.ru/api/v1/chat/completions")
LLM_MODEL = getattr(settings, "LLM_MODEL", "GigaChat")
LLM_AUTH_URL = getattr(settings, "LLM_AUTH_URL", "https://ngw.devices.sberbank.ru:9443/api/v2/oauth")
LLM_API_KEY = getattr(settings, "LLM_API_KEY", "")  # Base64(client_id:client_secret)

# ────────────── Путь к файлу с базовым промптом ──────────────
CRUD_PROMPT_FILE = "base/crud.md"

# ────────────── Асинхронное чтение промпта ──────────────
async def read_prompt() -> str:
    """Асинхронное чтение промпта из файла base/crud.md."""
    if os.path.exists(CRUD_PROMPT_FILE):
        async with aiofiles.open(CRUD_PROMPT_FILE, mode="r", encoding="utf-8") as f:
            return await f.read()
    return "You are a SQL generator for a notes application."

# ────────────── Получение Access Token для GigaChat ──────────────
async def get_gigachat_token() -> str:
    """Получает Access Token от GigaChat OAuth (действует 30 минут)."""
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "RqUID": str(uuid.uuid4()),
        "Authorization": f"Basic {LLM_API_KEY}"
    }
    payload = {"scope": "GIGACHAT_API_PERS"}
    
    # verify=False отключает проверку SSL (нужно для dev-сертификатов Сбера)
    async with httpx.AsyncClient(timeout=30, verify=False) as client:
        resp = await client.post(LLM_AUTH_URL, headers=headers, data=payload)
        if resp.status_code != 200:
            raise RuntimeError(f"GigaChat OAuth error: {resp.status_code} - {resp.text}")
        return resp.json()["access_token"]

# ────────────── Извлечение чистого SQL из ответа LLM ──────────────
def extract_sql_from_response(text: str, user_id: int) -> str:
    """Надёжно извлекает SQL-запрос, игнорируя markdown и артефакты."""
    text = text.strip()
    
    # 1. Убираем блоки кода markdown
    if "```sql" in text:
        text = text.split("```sql")[-1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[-1].split("```")[0].strip()

    # 2. Ищем SQL-команду до точки с запятой или конца строки
    sql_pattern = r'(SELECT|INSERT|UPDATE|DELETE)\s*[^;]*(?:;|$)'
    match = re.search(sql_pattern, text, re.IGNORECASE | re.DOTALL)
    
    if match:
        sql = match.group(0).strip()
        # 3. Агрессивная очистка хвоста: убираем обратные кавычки, кавычки, слеши, пробелы
        sql = re.sub(r'[`\'"\\;\s]+$', '', sql)
        if not sql.endswith(';'):
            sql += ';'
        return sql
    
    # 4. Фолбэк: безопасный запрос на случай сбоя парсинга
    return f"SELECT * FROM note WHERE user_id = {user_id} LIMIT 10;"

# ────────────── Вызов LLM с user_id ──────────────
async def call_gpt(
    user_request: str,
    user_id: int,
    request: Request,
    temperature: float = 0.7,
    max_tokens: int = 300
) -> str:
    """Асинхронный вызов GPT для генерации SQL с учётом user_id и даты."""
    log = request.app.state.log

    try:
        await log.log_info(target="GPT CRUD", message=f"Получен запрос: {user_request}")
        await log.log_info(target="GPT CRUD", message=f"user_id: {user_id}")

        # Получаем токен и текущую дату
        access_token = await get_gigachat_token()
        current_date = datetime.now().strftime("%Y-%m-%d")
        base_prompt = await read_prompt()

        # ────────────── Строгий промпт с примерами дат (требование Pro) ──────────────
        full_prompt = f"""
{base_prompt}

Ты — генератор SQL-запросов SQLite для таблицы заметок (note).
Твоя задача: преобразовать запрос пользователя в ОДИН валидный SQL-запрос.

ПРАВИЛА:
1. Возвращай ТОЛЬКО чистый SQL. Без объяснений, без комментариев, без markdown.
2. Все запросы обязаны фильтроваться по user_id = {user_id}.
3. Для поиска по тексту используй: LIKE '%слово%'.
4. Поле для дат: created_at (тип DATETIME).

ПРИМЕРЫ ГЕНЕРАЦИИ ЗАПРОСОВ ПО ДАТАМ:
- "заметки за текущий месяц" -> SELECT * FROM note WHERE user_id = {user_id} AND strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now');
- "заметки за прошлый месяц" -> SELECT * FROM note WHERE user_id = {user_id} AND strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now', '-1 month');
- "заметки за январь 2026 года" -> SELECT * FROM note WHERE user_id = {user_id} AND strftime('%Y-%m', created_at) = '2026-01';
- "заметки за сегодня" -> SELECT * FROM note WHERE user_id = {user_id} AND date(created_at) = date('now');
- "заметки за неделю" -> SELECT * FROM note WHERE user_id = {user_id} AND created_at >= datetime('now', '-7 days');

Текущая дата: {current_date}
Запрос пользователя: {user_request}

Ответ (ТОЛЬКО SQL):
"""

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        payload = {
            "model": LLM_MODEL,
            "messages": [{"role": "user", "content": full_prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        # Отправка запроса к GigaChat
        async with httpx.AsyncClient(timeout=60, verify=False) as client:
            resp = await client.post(LLM_BASE_URL, headers=headers, json=payload)
            if resp.status_code != 200:
                raise RuntimeError(f"LLM API error: {resp.status_code} - {resp.text}")
            
            data = resp.json()
            try:
                if "choices" in data and data["choices"]:
                    raw_response = data["choices"][0]["message"]["content"]
                elif "output" in data and data["output"]:
                    raw_response = data["output"][0]["content"][0]["text"]
                else:
                    raise KeyError("Неизвестный формат ответа")
            except (KeyError, IndexError, TypeError) as e:
                raise RuntimeError(f"Unexpected LLM response format: {data}")

        # Извлекаем и возвращаем чистый SQL
        sql_query = extract_sql_from_response(raw_response, user_id)
        await log.log_info(target="GPT CRUD", message=f"✅ Сгенерирован SQL:\n{sql_query}")
        return sql_query

    except Exception as e:
        await log.log_error(target="GPT CRUD", message=f"❌ Ошибка call_gpt: {str(e)}")
        raise

# ────────────── Выполнение SQL ──────────────
async def execute_sql(sql: str, db: AsyncSession, request: Request) -> Dict:
    """Выполнение SQL-запроса через SQLAlchemy AsyncSession."""
    log = request.app.state.log
    await log.log_info(target="GPT CRUD", message=f"SQL от GPT (raw): {sql}")

    if not sql:
        raise ValueError("Пустой SQL-запрос")

    # Двойная очистка на всякий случай
    cleaned_sql = sql.replace("```sql", "").replace("```", "").strip()
    cleaned_sql = re.sub(r'[`\'"\\;\s]+$', '', cleaned_sql)
    if not cleaned_sql.endswith(';'):
        cleaned_sql += ';'

    sql_type = cleaned_sql.split()[0].upper()

    try:
        if sql_type == "SELECT":
            result = await db.execute(text(cleaned_sql))
            rows = result.mappings().all()
            await log.log_info(target="GPT CRUD", message=f"✅ Найдено заметок: {len(rows)}")
            return {"sql": cleaned_sql, "rows": rows}

        # INSERT / UPDATE / DELETE
        await db.execute(text(cleaned_sql))
        await db.commit()
        message = {
            "INSERT": "Заметка добавлена",
            "UPDATE": "Заметка обновлена",
            "DELETE": "Заметка удалена"
        }.get(sql_type, "Запрос выполнен")
        
        return {"sql": cleaned_sql, "message": message}

    except Exception as e:
        await db.rollback()
        await log.log_error(target="GPT CRUD", message=f"❌ Ошибка SQL: {str(e)}")
        raise