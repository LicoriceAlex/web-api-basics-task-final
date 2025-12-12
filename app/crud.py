from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from . import schemas
from .models import Currency, Rate


async def list_currencies(session: AsyncSession) -> list[Currency]:
    """Список всех пар"""
    result = await session.scalars(select(Currency).order_by(Currency.id))
    return result.all()


async def get_currency(session: AsyncSession, currency_id: int) -> Optional[Currency]:
    """Пара по id"""
    result = await session.scalars(select(Currency).where(Currency.id == currency_id))
    return result.first()


async def get_currency_by_code(session: AsyncSession, code: str) -> Optional[Currency]:
    """Пара по коду"""
    result = await session.scalars(select(Currency).where(Currency.code == code))
    return result.first()


async def create_currency(session: AsyncSession, data: schemas.CurrencyCreate) -> Currency:
    """Создать новую пару"""
    currency = Currency(code=data.code.upper(), name=data.name, enabled=data.enabled)
    session.add(currency)
    await session.commit()
    await session.refresh(currency)
    return currency


async def update_currency(
    session: AsyncSession, currency: Currency, data: schemas.CurrencyUpdate
) -> Currency:
    """Обновить пару"""
    if data.name is not None:
        currency.name = data.name
    if data.enabled is not None:
        currency.enabled = data.enabled

    session.add(currency)
    await session.commit()
    await session.refresh(currency)
    return currency


async def delete_currency(session: AsyncSession, currency: Currency) -> None:
    """Удалить пару"""
    await session.delete(currency)
    await session.commit()


async def list_rates(
    session: AsyncSession, currency_code: str, limit: int = 50
) -> list[Rate]:
    """История цен по коду пары"""
    stmt = (
        select(Rate)
        .where(Rate.currency_code == currency_code.upper())
        .order_by(Rate.fetched_at.desc())
        .limit(limit)
    )
    result = await session.scalars(stmt)
    return result.all()


async def get_latest_rate(session: AsyncSession, currency_code: str) -> Optional[Rate]:
    """Последняя цена по коду пары"""
    stmt = (
        select(Rate)
        .where(Rate.currency_code == currency_code.upper())
        .order_by(Rate.fetched_at.desc())
        .limit(1)
    )
    result = await session.scalars(stmt)
    return result.first()


async def create_rate(
    session: AsyncSession,
    *,
    currency_code: str,
    nominal: int,
    value: float,
    fetched_at: datetime,
    source: str,
) -> Rate:
    """Создать запись с ценой"""
    rate = Rate(
        currency_code=currency_code.upper(),
        nominal=nominal,
        value=value,
        fetched_at=fetched_at,
        source=source,
    )
    session.add(rate)
    await session.commit()
    await session.refresh(rate)
    return rate
