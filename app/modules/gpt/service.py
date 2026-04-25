# app/modules/gpt/service.py

"""
Сервисный слой для обращения к LLM (GPT-модели) через Responses API.

Назначение:
1. Асинхронные запросы к внешнему API LLM
2. Отделение бизнес-логики от маршрутов (routes)
3. Возврат текста модели в стандартизированном виде

Использование:
    from app.modules.gpt.service import call_gpt
    answer = await call_gpt("Привет, расскажи стих")
"""

import httpx
from app.config import settings

# Настройки LLM берём из config.py
LLM_BASE_URL = getattr(settings, "LLM_BASE_URL", "https://api.openai.com/v1/responses")
LLM_MODEL = getattr(settings, "LLM_MODEL", "gpt-4o-mini")
LLM_API_KEY = getattr(settings, "LLM_API_KEY", "")


async def call_gpt(prompt: str, temperature: float = 0.7, max_tokens: int = 300) -> str:
    """
    Асинхронный вызов GPT-модели через Responses API.
    
    Параметры:
    - prompt: str — текст запроса от пользователя
    - temperature: float — креативность ответа (0–2)
    - max_tokens: int — максимальное количество токенов в ответе

    Возвращает:
    - str: текст ответа модели

    Исключения:
    - RuntimeError: при ошибке LLM API или некорректном формате ответа
    """
    headers = {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": LLM_MODEL,
        "input": prompt,            # Responses API теперь использует 'input', а не 'messages'
        "temperature": temperature,
        "max_output_tokens": max_tokens
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(LLM_BASE_URL, headers=headers, json=payload)

        if resp.status_code != 200:
            raise RuntimeError(f"Ошибка при вызове LLM: LLM API error: {resp.status_code}, {resp.text}")

        data = resp.json()
        try:
            # Извлекаем текст ответа из структуры Responses API
            answer = data["output"][0]["content"][0]["text"]
        except (KeyError, IndexError, TypeError):
            raise RuntimeError(f"Unexpected LLM response format: {data}")

        return answer