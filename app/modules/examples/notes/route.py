# app/modules/examples/notes/route.py

"""
Маршруты для работы с заметками (CRUD) с логированием.
Используется in-memory "БД" через словарь:
- ключ = id
- значение = объект Note
Это позволяет быстро получать, обновлять и удалять заметку по id.
"""

from fastapi import APIRouter, HTTPException, status, Request
from .schema import Note, NoteCreate, NoteUpdate

router = APIRouter(prefix="/examples/notes", tags=["examples_notes"])

# In-memory "БД" в виде словаря
notes_db: dict[int, Note] = {}
note_id_counter = 1


@router.get(
    "/",
    response_model=list[Note],
    status_code=status.HTTP_200_OK,
    summary="Получить все заметки"
)
async def get_notes(request: Request):
    """
    GET /notes
    Возвращает список всех заметок.
    """
    notes = list(notes_db.values())
    await request.app.state.log.log_info("notes", "Получение всех заметок", {"count": len(notes)})
    return notes


@router.post(
    "/",
    response_model=Note,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новую заметку"
)
async def create_note(request: Request, note: NoteCreate):
    """
    POST /notes
    Создаёт новую заметку.
    id генерируется автоматически сервером.
    """
    global note_id_counter

    new_note = Note(
        id=note_id_counter,
        title=note.title,
        content=note.content
    )

    notes_db[note_id_counter] = new_note
    note_id_counter += 1

    await request.app.state.log.log_info("notes", "Создана новая заметка", new_note.dict())
    return new_note


@router.get(
    "/{note_id}",
    response_model=Note,
    status_code=status.HTTP_200_OK,
    summary="Получить заметку по ID"
)
async def get_note(request: Request, note_id: int):
    """
    GET /notes/{id}
    Получает заметку по её идентификатору.
    """
    note = notes_db.get(note_id)
    if not note:
        await request.app.state.log.log_error("notes", f"Заметка с id={note_id} не найдена")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Заметка не найдена")

    await request.app.state.log.log_info("notes", f"Получена заметка id={note_id}", note.dict())
    return note


@router.patch(
    "/{note_id}",
    response_model=Note,
    status_code=status.HTTP_200_OK,
    summary="Частично обновить заметку"
)
async def patch_note(request: Request, note_id: int, data: NoteUpdate):
    """
    PATCH /notes/{id}
    Частичное обновление заметки (обновляются только переданные поля).
    """
    note = notes_db.get(note_id)
    if not note:
        await request.app.state.log.log_error("notes", f"Заметка с id={note_id} не найдена для обновления")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Заметка не найдена")

    if data.title is not None:
        note.title = data.title
    if data.content is not None:
        note.content = data.content

    await request.app.state.log.log_info("notes", f"Обновлена заметка id={note_id}", note.dict())
    return note


@router.put(
    "/{note_id}",
    response_model=Note,
    status_code=status.HTTP_200_OK,
    summary="Полностью заменить заметку"
)
async def put_note(request: Request, note_id: int, data: NoteCreate):
    """
    PUT /notes/{id}
    Полная замена заметки.
    Все поля обязательны.
    """
    if note_id not in notes_db:
        await request.app.state.log.log_error("notes", f"Заметка с id={note_id} не найдена для замены")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Заметка не найдена")

    updated_note = Note(
        id=note_id,
        title=data.title,
        content=data.content
    )

    notes_db[note_id] = updated_note
    await request.app.state.log.log_info("notes", f"Полностью заменена заметка id={note_id}", updated_note.dict())
    return updated_note


@router.delete(
    "/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить заметку"
)
async def delete_note(request: Request, note_id: int):
    """
    DELETE /notes/{id}
    Удаляет заметку по идентификатору.
    """
    if note_id not in notes_db:
        await request.app.state.log.log_error("notes", f"Заметка с id={note_id} не найдена для удаления")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Заметка не найдена")

    del notes_db[note_id]
    await request.app.state.log.log_info("notes", f"Удалена заметка id={note_id}")
