from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from ..db.database import Base


class Currency(Base):
    """Пара для отслеживания"""
    __tablename__ = "currencies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(length=20), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(length=200), default="", server_default="")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Rate(Base):
    """Запись цены в определенный момент времени"""
    __tablename__ = "rates"

    __table_args__ = (
        UniqueConstraint("currency_code", "fetched_at", "source", name="uq_rate_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    currency_code: Mapped[str] = mapped_column(String(length=20), index=True)
    nominal: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    value: Mapped[float] = mapped_column(Float)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    source: Mapped[str] = mapped_column(
        String(length=200), default="cbr", server_default="cbr"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
