# app/modules/notes/route_user.py

"""
Маршруты для работы с заметками (CRUD) с логированием.
Используется база данных через SQLAlchemy (AsyncSession).

ВАЖНО:
- Все маршруты защищены авторизацией
- Пользователь работает ТОЛЬКО со своими заметками
- Доступ к чужим заметкам запрещён

Операции:
- создание заметки
- получение списка заметок пользователя
- получение заметки по id
- частичное обновление
- полная замена
- удаление
"""

from fastapi import APIRouter, HTTPException, status, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.modules.notes.schema import Note, NoteCreate, NoteUpdate
from app.modules.notes.model import Note as NoteModel
from app.modules.auth.model import User as UserModel
from app.modules.auth.route import get_current_user
from app.utils.database import get_db

router = APIRouter(prefix="/notes", tags=["notes"])


@router.get(
    "/",
    response_model=list[Note],
    status_code=status.HTTP_200_OK,
    summary="Получить все заметки пользователя"
)
async def get_notes(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    GET /notes
    Возвращает список заметок ТЕКУЩЕГО пользователя.
    """
    result = await db.execute(
        select(NoteModel).where(NoteModel.user_id == current_user.id)
    )
    notes = result.scalars().all()

    await request.app.state.log.log_info(
        "notes",
        "Получение заметок пользователя",
        {"user_id": current_user.id, "count": len(notes)}
    )

    return notes


@router.post(
    "/",
    response_model=Note,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новую заметку"
)
async def create_note(
    request: Request,
    note: NoteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    POST /notes
    Создаёт новую заметку и привязывает её к текущему пользователю.
    """
    db_note = NoteModel(
        title=note.title,
        content=note.content,
        user_id=current_user.id
    )

    db.add(db_note)
    await db.commit()
    await db.refresh(db_note)

    await request.app.state.log.log_info(
        "notes",
        "Создана новая заметка",
        {"id": db_note.id, "user_id": current_user.id}
    )

    return db_note


@router.get(
    "/{note_id}",
    response_model=Note,
    status_code=status.HTTP_200_OK,
    summary="Получить заметку по ID"
)
async def get_note(
    request: Request,
    note_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    GET /notes/{id}
    Получает заметку по id, ТОЛЬКО если она принадлежит пользователю.
    """
    result = await db.execute(
        select(NoteModel).where(
            NoteModel.id == note_id,
            NoteModel.user_id == current_user.id
        )
    )
    note = result.scalar_one_or_none()

    if not note:
        await request.app.state.log.log_error(
            "notes",
            f"Доступ запрещён или заметка не найдена (id={note_id})"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заметка не найдена"
        )

    await request.app.state.log.log_info(
        "notes",
        "Получена заметка",
        {"id": note_id, "user_id": current_user.id}
    )

    return note


@router.patch(
    "/{note_id}",
    response_model=Note,
    status_code=status.HTTP_200_OK,
    summary="Частично обновить заметку"
)
async def patch_note(
    request: Request,
    note_id: int,
    data: NoteUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    PATCH /notes/{id}
    Частичное обновление заметки пользователя.
    """
    result = await db.execute(
        select(NoteModel).where(
            NoteModel.id == note_id,
            NoteModel.user_id == current_user.id
        )
    )
    note = result.scalar_one_or_none()

    if not note:
        await request.app.state.log.log_error(
            "notes",
            f"Попытка обновления чужой или несуществующей заметки (id={note_id})"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заметка не найдена"
        )

    if data.title is not None:
        note.title = data.title
    if data.content is not None:
        note.content = data.content

    await db.commit()
    await db.refresh(note)

    await request.app.state.log.log_info(
        "notes",
        "Обновлена заметка",
        {"id": note_id, "user_id": current_user.id}
    )

    return note


@router.put(
    "/{note_id}",
    response_model=Note,
    status_code=status.HTTP_200_OK,
    summary="Полностью заменить заметку"
)
async def put_note(
    request: Request,
    note_id: int,
    data: NoteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    PUT /notes/{id}
    Полная замена заметки пользователя.
    """
    result = await db.execute(
        select(NoteModel).where(
            NoteModel.id == note_id,
            NoteModel.user_id == current_user.id
        )
    )
    note = result.scalar_one_or_none()

    if not note:
        await request.app.state.log.log_error(
            "notes",
            f"Попытка замены чужой или несуществующей заметки (id={note_id})"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заметка не найдена"
        )

    note.title = data.title
    note.content = data.content

    await db.commit()
    await db.refresh(note)

    await request.app.state.log.log_info(
        "notes",
        "Полностью заменена заметка",
        {"id": note_id, "user_id": current_user.id}
    )

    return note


@router.delete(
    "/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить заметку"
)
async def delete_note(
    request: Request,
    note_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    DELETE /notes/{id}
    Удаляет заметку пользователя.
    """
    result = await db.execute(
        select(NoteModel).where(
            NoteModel.id == note_id,
            NoteModel.user_id == current_user.id
        )
    )
    note = result.scalar_one_or_none()

    if not note:
        await request.app.state.log.log_error(
            "notes",
            f"Попытка удаления чужой или несуществующей заметки (id={note_id})"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заметка не найдена"
        )

    await db.delete(note)
    await db.commit()

    await request.app.state.log.log_info(
        "notes",
        "Удалена заметка",
        {"id": note_id, "user_id": current_user.id}
    )

    return None
