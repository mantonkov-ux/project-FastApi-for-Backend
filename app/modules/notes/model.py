# app/modules/notes/model.py

from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.utils.database import Base


class Note(Base):
    """
    ORM-модель заметки.

    Отражает таблицу note в базе данных.
    Используется для:
    - создания заметок
    - чтения данных
    - обновления и удаления записей
    """

    __tablename__ = "note"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=True)

    # Связь с пользователем
    user = relationship("User", back_populates="notes")
