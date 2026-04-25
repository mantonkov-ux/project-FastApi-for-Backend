# app/modules/gpt_crud/route.py

"""
Маршруты GPT CRUD для заметок.

Назначение:
1. Получение запроса пользователя и генерация SQL через LLM
2. Асинхронное выполнение SQL-запросов через базу данных
3. Защита маршрутов авторизацией пользователя
4. Возврат результата пользователю в JSON формате
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.gpt_crud.service import call_gpt, execute_sql
from app.utils.database import get_db
from app.modules.auth.route import get_current_user
from app.modules.gpt_crud.schema import GPTCRUDRequest, GPTCRUDResponse

router = APIRouter(prefix="/gpt_crud", tags=["GPT CRUD"])

@router.post("/", response_model=GPTCRUDResponse, status_code=status.HTTP_200_OK)
async def gpt_crud_endpoint(
    request: Request,
    user_request: GPTCRUDRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    POST /gpt_crud
    Генерирует SQL-запрос на основе пользовательского запроса через LLM
    и выполняет его в базе данных, возвращая результат.

    Аргументы:
    - user_request: GPTCRUDRequest — текст запроса от пользователя
    - current_user: текущий авторизованный пользователь
    - db: асинхронная сессия SQLAlchemy

    Особенности:
    - Пользователь должен быть авторизован
    - В prompt передаётся запрос типа:
        "Запомни тему вебинара 'Тема вебинара о FastAPI'"
        "Сохрани контакты менеджера по созданию сайта"
        "Напомни что я должен был сделать к пятнице"
        "Напомни контакты менеджера по сайту"
    - SQL-запрос формируется с учётом user_id
    """
    try:
        # 1. Генерация SQL-запроса через GPT с учётом user_id
        sql_query = await call_gpt(user_request.prompt, user_id=current_user.id, request=request)

        # 2. Выполнение SQL в базе
        results = await execute_sql(sql_query, db, request=request)

        # 3. Возврат ответа 
        return GPTCRUDResponse(
            sql=results.get("sql"),
            rows=results.get("rows"),
            message=results.get("message")
        )

    except Exception as e:
        # Возвращаем понятный detail пользователю
        raise HTTPException(status_code=500, detail=f"Ошибка при вызове GPT CRUD: {str(e)}")
