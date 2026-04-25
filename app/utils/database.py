# database.py

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config import settings
from sqlalchemy.orm import declarative_base
from sqlalchemy.future import select
from app.utils.security import hash_password

# Создаём Base
Base = declarative_base()

# Берём URL из настроек
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# Асинхронный движок
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=True
)

# Асинхронная сессия
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Dependency для FastAPI
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# Инициализация базы данных
async def init_db(logger):

    # Создаём таблицы
    from app.modules.notes.model import Note
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Проверяем наличие админа
    from app.modules.auth.model import User    
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()

        if not any(u.is_admin for u in users):
            # Проверяем, есть ли уже логин 'admin'
            if any(u.login == "admin" for u in users):
                admin_user = next(u for u in users if u.login == "admin")
                admin_user.is_admin = True
                session.add(admin_user)
                await session.commit()
                await session.refresh(admin_user)
                await logger.log_info("db", "Существующий пользователь 'admin' стал администратором")
            else:
                # Создаём первого админа
                admin_user = User(
                    name="Administrator",
                    login="admin",
                    password=hash_password("admin"),
                    is_admin=True
                )
                session.add(admin_user)
                await session.commit()
                await session.refresh(admin_user)
                await logger.log_info("db", f"Создан первый админ: {admin_user.login}")

# Закрытие базы данных
async def close_db():
    await engine.dispose()
