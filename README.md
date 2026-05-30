# ⚡ FastAPI Backend — REST API с авторизацией и базой данных

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-latest-green.svg)](https://fastapi.tiangolo.com)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-red.svg)](https://sqlalchemy.org)
[![JWT](https://img.shields.io/badge/Auth-JWT-orange.svg)](https://jwt.io)
[![Alembic](https://img.shields.io/badge/Migrations-Alembic-blue.svg)](https://alembic.sqlalchemy.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Готовый шаблон backend-сервиса** на FastAPI с регистрацией и авторизацией пользователей (JWT), подключением к БД, миграциями и интеграцией LLM. Основа для любого веб-приложения, Telegram-бота или AI-сервиса.

---

## 🎯 Для кого

| Задача | Что даёт этот backend |
|---|---|
| Нужен API для мобильного приложения | Готовые эндпоинты, документация Swagger из коробки |
| Telegram-бот с личным кабинетом | Регистрация, авторизация, хранение данных пользователей |
| AI-сервис с историей запросов | БД + JWT + подключение к LLM в одном проекте |
| Стартап ищет быстрый MVP | Шаблон разворачивается за 10 минут |

---

## ✨ Что реализовано

- 🔐 **Регистрация и авторизация** пользователей через JWT-токены
- 🛡️ **Защищённые маршруты** — приватные эндпоинты через `Depends`
- 🗄️ **База данных** через SQLAlchemy (async) + Alembic для миграций
- ✅ **Валидация данных** — Pydantic v2, типизированные схемы запросов и ответов
- 🤖 **Интеграция LLM** — AI-ассистент выполняет CRUD-операции через естественный язык
- 📖 **Автодокументация** — Swagger UI и ReDoc доступны сразу после запуска
- ⚡ **Асинхронность** — aiosqlite, aiologger, неблокирующие запросы к БД
- 🔒 **Безопасность** — хеширование паролей через passlib, ключи в `.env`

---

## 🏗️ Архитектура

```
project-FastApi-for-Backend/
├── app/
│   ├── routers/          # Маршруты API (users, auth, items...)
│   ├── services/         # Бизнес-логика
│   ├── models/           # SQLAlchemy-модели (таблицы БД)
│   ├── schemas/          # Pydantic-схемы (валидация)
│   └── dependencies.py   # JWT-авторизация через Depends
├── base/                 # Конфигурация БД и базовые классы
├── alembic/              # Миграции базы данных
├── .env_example
└── requirements.txt
```

**Стек:**
- **Framework:** FastAPI + Uvicorn
- **База данных:** SQLAlchemy 2.0 (async) + aiosqlite / PostgreSQL
- **Миграции:** Alembic
- **Авторизация:** PyJWT + passlib (bcrypt)
- **Валидация:** Pydantic v2 + pydantic-settings
- **LLM:** OpenAI / GigaChat (SQL-запросы через AI)

---

## 🚀 Быстрый старт

### 1. Клонировать и установить зависимости

```bash
git clone https://github.com/mantonkov-ux/project-FastApi-for-Backend.git
cd project-FastApi-for-Backend
python -m venv .venv
# Windows: .venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Настроить переменные окружения

Скопируйте `.env_example` в `.env`:

```env
DATABASE_URL=sqlite+aiosqlite:///./app.db
SECRET_KEY=ваш_секретный_ключ_jwt
OPENAI_API_KEY=ваш_ключ_openai   # опционально, для LLM-функций
```

### 3. Применить миграции и запустить

```bash
alembic upgrade head
uvicorn app.main:app --reload
```

### 4. Открыть документацию API

- Swagger UI: **http://127.0.0.1:8000/docs**
- ReDoc: **http://127.0.0.1:8000/redoc**

---

## 🔑 Пример авторизации

```bash
# Регистрация
POST /auth/register
{"username": "ivan", "password": "secret123"}

# Вход — получить JWT-токен
POST /auth/login
{"username": "ivan", "password": "secret123"}
→ {"access_token": "eyJ...", "token_type": "bearer"}

# Защищённый маршрут с токеном
GET /users/me
Authorization: Bearer eyJ...
→ {"id": 1, "username": "ivan"}
```

---

## 🤖 LLM-интеграция

Проект включает AI-ассистента, который работает с базой данных через естественный язык:

```python
# Вместо SQL-запроса — просто описание на русском
result = await ai_assistant.query(
    "Найди всех пользователей, зарегистрированных на этой неделе"
)
# AI генерирует корректный SQL и возвращает результат
```

---

## 💼 Заказать backend для вашего проекта

Разрабатываю на заказ:

- 🔌 REST API любой сложности под ваше приложение или бота
- 👤 Система авторизации (JWT, OAuth2, социальные сети)
- 🗄️ Проектирование и настройка базы данных (SQLite → PostgreSQL)
- 🤖 Интеграция AI/LLM в ваш существующий backend
- 📦 Деплой на сервер (VPS, Railway, Render)

**📩 Написать мне:** [Kwork-профиль](https://kwork.ru) | [GitHub](https://github.com/mantonkov-ux)

---

## 📄 Лицензия

MIT — используйте как шаблон для своих проектов.

---

*Проект разработан в рамках обучения в [Университете Искусственного Интеллекта](https://university.ai) (Москва) по специальности GPT Engineer.*
