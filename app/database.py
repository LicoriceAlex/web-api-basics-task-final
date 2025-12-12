import os
from pathlib import Path
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

# База по умолчанию лежит рядом с проектом
DEFAULT_DB_PATH = (Path(__file__).resolve().parent.parent / "currency.db").as_posix()
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{DEFAULT_DB_PATH}")

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
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
