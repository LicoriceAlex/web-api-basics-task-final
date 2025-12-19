from pathlib import Path
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from ..config import settings

# База по умолчанию лежит рядом с проектом
DEFAULT_DB_PATH = settings.default_db_path
DATABASE_URL = settings.database_url

engine = create_async_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    """Базовый класс для моделей SQLAlchemy"""


async def get_session() -> AsyncIterator[AsyncSession]:
    """Сессия базы для FastAPI"""
    async with SessionLocal() as session:
        yield session


async def init_db() -> None:
    """Создать таблицы если их нет"""
    from ..models import orm as _orm

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
