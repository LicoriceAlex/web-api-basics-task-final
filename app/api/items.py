from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.crud import (
    create_currency,
    delete_currency,
    get_currency,
    list_currencies,
    update_currency,
)
from ..db.database import get_session
from ..models.schemas import CurrencyCreate, CurrencyRead, CurrencyUpdate

router = APIRouter(tags=["items"])


@router.get("/items", response_model=list[CurrencyRead])
async def list_items(session: AsyncSession = Depends(get_session)):
    items = await list_currencies(session)
    return [CurrencyRead.model_validate(item) for item in items]


@router.get("/items/{item_id}", response_model=CurrencyRead)
async def get_item_api(item_id: int, session: AsyncSession = Depends(get_session)):
    item = await get_currency(session, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return CurrencyRead.model_validate(item)


@router.post("/items", response_model=CurrencyRead, status_code=201)
async def create_item_api(
    payload: CurrencyCreate,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    try:
        item = await create_currency(session, payload)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Currency code already exists")

    item_view = CurrencyRead.model_validate(item)
    await request.app.state.nats.emit("item_created", item_view.model_dump())
    return item_view


@router.patch("/items/{item_id}", response_model=CurrencyRead)
async def update_item_api(
    item_id: int,
    payload: CurrencyUpdate,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    item = await get_currency(session, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    item = await update_currency(session, item, payload)
    item_view = CurrencyRead.model_validate(item)
    await request.app.state.nats.emit("item_updated", item_view.model_dump())
    return item_view


@router.delete("/items/{item_id}", status_code=204)
async def delete_item_api(
    item_id: int,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    item = await get_currency(session, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    await delete_currency(session, item)
    await request.app.state.nats.emit("item_deleted", {"id": item_id})
    return None
