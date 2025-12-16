from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.crud import get_latest_rate, list_rates
from ..db.database import get_session
from ..models.schemas import RateRead

router = APIRouter(tags=["rates"])


@router.get("/rates", response_model=list[RateRead])
async def list_rates_api(
    session: AsyncSession = Depends(get_session),
    code: str = Query(..., min_length=1, max_length=20),
    limit: int = Query(50, ge=1, le=500),
):
    rates = await list_rates(session, code, limit=limit)
    return [RateRead.model_validate(rate) for rate in rates]


@router.get("/rates/latest", response_model=Optional[RateRead])
async def get_latest_rate_api(
    session: AsyncSession = Depends(get_session),
    code: str = Query(..., min_length=1, max_length=20),
):
    rate = await get_latest_rate(session, code)
    if not rate:
        return None
    return RateRead.model_validate(rate)

