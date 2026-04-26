# app/modules/goods/model.py
from sqlalchemy import Column, Integer, String
from app.utils.database import Base  # Импортируем базовый класс

class Good(Base):
    __tablename__ = "good"  # 🔤 Имя таблицы — маленькими буквами!
    
    id = Column(Integer, primary_key=True, index=True)  # 🔢 Авто-номер
    name = Column(String(100), nullable=False)          # 🏷️ Название товара