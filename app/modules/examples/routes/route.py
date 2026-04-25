# app/modules/examples/routes/route.py

# Импортируем необходимые классы и константы из FastAPI
from fastapi import APIRouter, Body, HTTPException, status
# Импортируем типы для аннотации — это улучшает читаемость и поддержку кода
from typing import Dict, Any, Optional

# Создаём экземпляр роутера — он будет группировать маршруты этого модуля
router = APIRouter(
    prefix="/examples/routes",     # Общий префикс для всех маршрутов из роутера
    tags=["examples_routes"]       # Тег для группировки в документации    
)

# 1. Простой GET (без параметров)
@router.get("/hello")
def hello():
    return {"message": "Hello from examples/routes!"}

# 2. GET с параметром пути
@router.get("/square/{number}")
def square(number: int):
    return {"number": number, "square": number ** 2}

# 3. GET с query‑параметрами
@router.get("/search")
def search(q: str, limit: int = 10):
    return {"query": q, "limit": limit}

# Примеры маршрутов CRUD

# Глобальное хранилище ресурсов в памяти (для демонстрации CRUD)
# Тип: словарь, где ключ — int (ID ресурса), значение — словарь с данными ресурса
STORAGE: Dict[int, Dict[Any, Any]] = {}

# Счётчик для генерации уникальных ID
# Начинаем с 1, чтобы ID были положительными целыми
_current_id = 1

# Функция генерации уникального ID
# Используем global, так как меняем переменную вне локальной области
def generate_id() -> int:
    global _current_id
    _current_id += 1
    # Возвращаем предыдущее значение (до инкремента)
    return _current_id - 1

# 4. Маршрут: создание ресурса (POST /)
# status_code=status.HTTP_201_CREATED — явно указываем код ответа при успехе
@router.post("/", status_code=status.HTTP_201_CREATED)
def create(data: Dict[Any, Any] = Body(...)) -> Dict[str, Any]:
    """
    Создаёт новый ресурс в хранилище.
    
    Args:
        data: словарь с данными ресурса (из тела запроса).
    
    Returns:
        Словарь с статусом, сообщением и созданными данными.
    """
    # Проверяем, что тело запроса не пустое
    if not data:
        # Если данных нет — возвращаем ошибку 400 (неверный запрос)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Запрос не может быть пустым"
        )
    
    # Генерируем уникальный ID для нового ресурса
    item_id = generate_id()
    # Создаём полный ресурс: добавляем ID к переданным данным
    resource = {"id": item_id, **data}
    # Сохраняем ресурс в хранилище по ID
    STORAGE[item_id] = resource

    # Возвращаем ответ с статусом и данными
    return {
        "status": "created",
        "message": "Ресурс создан",
        "data": resource
    }

# 5. Маршрут: получение ресурса (GET /{item_id})
# status_code=status.HTTP_200_OK — код успеха для чтения
@router.get("/{item_id}", status_code=status.HTTP_200_OK)
def get_resource(item_id: int) -> Dict[Any, Any]:
    """
    Получает ресурс по ID.
    
    Args:
        item_id: ID ресурса (из параметра пути).
    
    Returns:
        Словарь с данными ресурса.
    """
    # Проверяем, существует ли ресурс с таким ID
    if item_id not in STORAGE:
        # Если нет — возвращаем ошибку 404
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ресурс с ID = {item_id} не найден"
        )
    # Если ресурс есть — возвращаем его данные
    return STORAGE[item_id]

# 6. Маршрут: обновление ресурса (PUT /{item_id})
# status_code=status.HTTP_200_OK — код успеха для обновления
@router.put("/{item_id}", status_code=status.HTTP_200_OK)
def update(item_id: int, data: Dict[Any, Any] = Body(...)) -> Dict[str, Any]:
    """
    Обновляет существующий ресурс по ID.
    
    Args:
        item_id: ID ресурса (из параметра пути).
        data: словарь с новыми данными (из тела запроса).
    
    Returns:
        Словарь с статусом, сообщением и обновлёнными данными.
    """
    # Проверяем, существует ли ресурс с таким ID
    if item_id not in STORAGE:
        # Если нет — возвращаем ошибку 404 (не найден)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ресурс с ID = {item_id} не найден"
        )
    
    # Проверяем, что тело запроса не пустое
    if not data:
        # Если данных нет — возвращаем ошибку 400
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Данные не могуть быть пустыми"
        )
    
    # Обновляем существующий ресурс: сливаем новые данные с текущими
    STORAGE[item_id].update(data)
    # Возвращаем ответ с статусом и обновлёнными данными
    return {
        "status": "updated",
        "message": f"Ресурс с ID = {item_id} обновлен",
        "data": STORAGE[item_id]
    }

# 7. Маршрут: удаление ресурса (DELETE /{item_id})
# status_code=status.HTTP_204_NO_CONTENT — код успеха без тела ответа
@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_resource(item_id: int):
    """
    Удаляет ресурс по ID.
    
    Args:
        item_id: ID ресурса (из параметра пути).
    
    Returns:
        None (статус 204 — нет тела ответа).
    """
    # Проверяем, существует ли ресурс с таким ID
    if item_id not in STORAGE:
        # Если нет — возвращаем ошибку 404
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ресурс с ID = {item_id} не найден"
        )
    
    # Удаляем ресурс из хранилища
    del STORAGE[item_id]
    # 204 — успех без тела ответа, поэтому return без значения
    return