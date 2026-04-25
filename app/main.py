# app/main.py

from fastapi import FastAPI             # Импортируем класс FastAPI из библиотеки FastAPI — он нужен для создания веб‑приложения
import uvicorn                          # Импортируем библиотеку uvicorn — это ASGI‑сервер, который будет запускать наше приложение
from .utils.log import Log              # Импорт логгера
from app.utils.database import init_db  # Инициализация базы данных
from app.utils.database import close_db # Закрытие базы данных

# Роуты
from .modules.examples.routes.route import router as examples_routes
from .modules.examples.notes.route import router as examples_notes
from .modules.notes.route_user import router as routes_notes
from .modules.auth.route import router as routes_auth
from .modules.gpt.route import router as routes_gpt
from .modules.gpt_crud.route import router as routes_gpt_crud

# Загрузка переменных окружения
from dotenv import load_dotenv
load_dotenv()

# Контекст управления жизненным циклом приложения
from contextlib import asynccontextmanager
@asynccontextmanager
async def lifespan(app: FastAPI):

    # Создание объекта логгера
    app.state.log = Log()

    # Лог запуска приложения
    await app.state.log.log_info(target="startup", message="Запуск приложения")

    # Инициализация базы данных
    await init_db(app.state.log)

    # Контекст приложения
    yield

    # Закрытие соединения с базой данных
    await close_db()

    # Лог остановки
    await app.state.log.log_info(target="startup", message="Остановка приложения")

    # Shutdown для корректного завершения работы асинхронных логгеров
    await app.state.log.shutdown()

# Создаём FastAPI приложение
app = FastAPI(lifespan=lifespan)

# Обработка COSR-запросов
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Эндпоинт "Обработчик GET-метода /"
@app.get("/")               # Декоратор, который регистрирует функцию как обработчик GET‑запросов к корневому пути `/`;
def root():                 # Определяем функцию‑обработчик для маршрута `/`;
                            # имя функции может быть любым, но должно быть уникальным в рамках модуля
    return {"message": "Hello, World!"}  # Возвращаем словарь в формате JSON — FastAPI автоматически преобразует его в HTTP‑ответ;

# Подключение маршрутов
app.include_router(examples_routes)
app.include_router(examples_notes)
app.include_router(routes_notes)
app.include_router(routes_auth)
app.include_router(routes_gpt)
app.include_router(routes_gpt_crud)
 
# Запуск
if __name__ == "__main__":  # Проверяем, запускается ли скрипт напрямую (а не импортируется как модуль)
    uvicorn.run(            # Вызываем функцию `run` из библиотеки Uvicorn — она запускает ASGI‑сервер
        "app.main:app",     # Строка формата 'модуль:объект': 
                            # - 'app' — имя пакета/папки, где лежит код;
                            # - 'main' — имя Python‑файла (без расширения .py), где определён объект приложения;
                            # - второй 'app' — имя объекта FastAPI (экземпляра класса `FastAPI`), объявленного в файле `main.py`
        host="127.0.0.1",   # Указываем IP‑адрес, на котором будет слушать сервер;
                            # '127.0.0.1' — локальный хост (только для текущего компьютера)
        port=8000,          # Задаём порт, на котором будет работать сервер; 8000 — распространённый выбор для разработки
        log_level="info",   # Устанавливаем уровень логирования: 'info' — будут выводиться информационные сообщения
                            # (например, о принятых запросах, ошибках и т. д.)
        reload=True         # Включаем режим автоперезагрузки: при изменении кода сервер автоматически перезапустится;
                            # удобно при разработке, но не рекомендуется для продакшена
    )