# app/modules/notes/route.py

"""
Маршруты для работы с заметками (CRUD) с логированием.
Используется база данных через SQLAlchemy (AsyncSession).

Операции:
- создание заметки
- получение списка заметок
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
from app.utils.database import get_db

router = APIRouter(prefix="/notes", tags=["notes"])


@router.get(
    "/",
    response_model=list[Note],
    status_code=status.HTTP_200_OK,
    summary="Получить все заметки"
)
async def get_notes(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    GET /notes
    Возвращает список всех заметок из базы данных.
    """
    result = await db.execute(select(NoteModel))
    notes = result.scalars().all()

    await request.app.state.log.log_info(
        "notes",
        "Получение всех заметок",
        {"count": len(notes)}
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
    db: AsyncSession = Depends(get_db)
):
    """
    POST /notes
    Создаёт новую заметку в базе данных.
    id генерируется автоматически сервером.
    """
    db_note = NoteModel(
        title=note.title,
        content=note.content
    )

    db.add(db_note)
    await db.commit()
    await db.refresh(db_note)

    await request.app.state.log.log_info(
        "notes",
        "Создана новая заметка",
        {"id": db_note.id, "title": db_note.title}
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
    db: AsyncSession = Depends(get_db)
):
    """
    GET /notes/{id}
    Получает заметку по её идентификатору.
    """
    result = await db.execute(
        select(NoteModel).where(NoteModel.id == note_id)
    )
    note = result.scalar_one_or_none()

    if not note:
        await request.app.state.log.log_error(
            "notes",
            f"Заметка с id={note_id} не найдена"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заметка не найдена"
        )

    await request.app.state.log.log_info(
        "notes",
        f"Получена заметка id={note_id}"
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
    db: AsyncSession = Depends(get_db)
):
    """
    PATCH /notes/{id}
    Частичное обновление заметки (обновляются только переданные поля).
    """
    result = await db.execute(
        select(NoteModel).where(NoteModel.id == note_id)
    )
    note = result.scalar_one_or_none()

    if not note:
        await request.app.state.log.log_error(
            "notes",
            f"Заметка с id={note_id} не найдена для обновления"
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
        f"Обновлена заметка id={note_id}"
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
    db: AsyncSession = Depends(get_db)
):
    """
    PUT /notes/{id}
    Полная замена заметки.
    Все поля обязательны.
    """
    result = await db.execute(
        select(NoteModel).where(NoteModel.id == note_id)
    )
    note = result.scalar_one_or_none()

    if not note:
        await request.app.state.log.log_error(
            "notes",
            f"Заметка с id={note_id} не найдена для замены"
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
        f"Полностью заменена заметка id={note_id}"
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
    db: AsyncSession = Depends(get_db)
):
    """
    DELETE /notes/{id}
    Удаляет заметку по идентификатору.
    """
    result = await db.execute(
        select(NoteModel).where(NoteModel.id == note_id)
    )
    note = result.scalar_one_or_none()

    if not note:
        await request.app.state.log.log_error(
            "notes",
            f"Заметка с id={note_id} не найдена для удаления"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заметка не найдена"
        )

    await db.delete(note)
    await db.commit()

    await request.app.state.log.log_info(
        "notes",
        f"Удалена заметка id={note_id}"
    )

    return None
