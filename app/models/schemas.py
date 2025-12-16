from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class CurrencyBase(BaseModel):
    """Общие поля пары"""
    code: str = Field(..., min_length=1, max_length=20)
    name: str = Field("", max_length=200)
    enabled: bool = True


class CurrencyCreate(CurrencyBase):
    """Создание пары"""
    pass


class CurrencyUpdate(BaseModel):
    """Обновление пары"""
    name: Optional[str] = Field(None, max_length=200)
    enabled: Optional[bool] = None

    model_config = {"extra": "forbid"}


class CurrencyRead(CurrencyBase):
    """Ответ с парой"""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RateRead(BaseModel):
    """Ответ с ценой"""
    id: int
    currency_code: str
    nominal: int
    value: float
    fetched_at: datetime
    source: str
    created_at: datetime

    model_config = {"from_attributes": True}


class NatsPublishRequest(BaseModel):
    type: str = Field(..., min_length=1, max_length=100)
    payload: Any = None


class NatsStatusRead(BaseModel):
    connected: bool
    url: str
    subject: str
    source_id: str
