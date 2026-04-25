# app/modules/auth/model.py

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.utils.database import Base


class User(Base):
    """
    ORM-модель пользователя.

    Отражает таблицу user в базе данных.
    Используется для:
    - регистрации и авторизации пользователей
    - проверки прав доступа (админ/не админ)
    - хранения основной информации о пользователе
    """

    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=True)
    login = Column(String(50), unique=True, nullable=True)
    password = Column(String(255), nullable=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Связь с заметками
    notes = relationship("Note", back_populates="user", cascade="all, delete-orphan")
