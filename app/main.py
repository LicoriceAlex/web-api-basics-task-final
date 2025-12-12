import logging
import os
from pathlib import Path
from typing import Annotated, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from . import crud, schemas
from .background import RatesUpdater
from .database import SessionLocal, get_session, init_db
from .nats_client import NatsClient
from .websockets import ConnectionManager

logger = logging.getLogger("currency_tracker")

# Менеджер активных WebSocket подключений
manager = ConnectionManager()

# Клиент NATS
nats = NatsClient(subject=os.getenv("NATS_SUBJECT", "items.updates"))

# Фоновая задача обновления цен
rates_updater = RatesUpdater(
    SessionLocal,
    notifier=nats.publish,
    interval_seconds=int(os.getenv("RATES_INTERVAL_SECONDS", "60")),
    source_url=os.getenv(
        "RATES_SOURCE_URL", "https://api.binance.com/api/v3/ticker/price"
    ),
)

app = FastAPI(
    title="Трекер цен криптовалют",
    description="REST API WebSocket фоновая задача NATS SQLite",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/ws-ui")
async def ws_ui():
    """HTML страница для просмотра WebSocket"""
    html_path = Path(__file__).resolve().parent / "static" / "ws.html"
    return FileResponse(html_path, media_type="text/html")


@app.on_event("startup")
async def on_startup() -> None:
    """Старт приложения"""
    await init_db()

    async def on_nats_event(event: dict) -> None:
        """Обработчик событий из NATS"""
        logger.info("NATS event received: %s", event.get("type"))
        await manager.broadcast(event)

    nats.set_on_event(on_nats_event)
    await nats.connect(required=True)

    await rates_updater.start()


@app.on_event("shutdown")
async def on_shutdown() -> None:
    """Остановка приложения"""
    await rates_updater.stop()
    await nats.close()


SessionDep = Annotated[AsyncSession, Depends(get_session)]


@app.get("/items", response_model=list[schemas.CurrencyRead])
async def list_items(session: SessionDep):
    """Список отслеживаемых пар"""
    items = await crud.list_currencies(session)
    return [schemas.CurrencyRead.model_validate(item) for item in items]


@app.get("/items/{item_id}", response_model=schemas.CurrencyRead)
async def get_item(item_id: int, session: SessionDep):
    """Получить одну пару по id"""
    item = await crud.get_currency(session, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return schemas.CurrencyRead.model_validate(item)


@app.post("/items", response_model=schemas.CurrencyRead, status_code=201)
async def create_item(payload: schemas.CurrencyCreate, session: SessionDep):
    """Создать пару для отслеживания"""
    try:
        item = await crud.create_currency(session, payload)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Currency code already exists")

    item_view = schemas.CurrencyRead.model_validate(item)
    await nats.publish({"type": "item_created", "payload": item_view.model_dump()})
    return item_view


@app.patch("/items/{item_id}", response_model=schemas.CurrencyRead)
async def update_item(item_id: int, payload: schemas.CurrencyUpdate, session: SessionDep):
    """Обновить пару"""
    item = await crud.get_currency(session, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    item = await crud.update_currency(session, item, payload)
    item_view = schemas.CurrencyRead.model_validate(item)
    await nats.publish({"type": "item_updated", "payload": item_view.model_dump()})
    return item_view


@app.delete("/items/{item_id}", status_code=204)
async def delete_item(item_id: int, session: SessionDep):
    """Удалить пару"""
    item = await crud.get_currency(session, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    await crud.delete_currency(session, item)
    await nats.publish({"type": "item_deleted", "payload": {"id": item_id}})
    return None


@app.post("/tasks/run")
async def run_background_task():
    """Ручной запуск фоновой задачи"""
    created = await rates_updater.run_once()
    return {
        "created_rates": created,
        "status": {
            "nats_connected": nats.is_connected,
            "rates_updater": rates_updater.status(),
        },
    }


@app.get("/tasks/status")
async def get_tasks_status():
    """Статус фоновой задачи и подключения к NATS"""
    return {"nats_connected": nats.is_connected, "rates_updater": rates_updater.status()}


@app.get("/rates", response_model=list[schemas.RateRead])
async def list_rates(
    session: SessionDep,
    code: str = Query(..., min_length=1, max_length=20),
    limit: int = Query(50, ge=1, le=500),
):
    """История цен по коду пары"""
    rates = await crud.list_rates(session, code, limit=limit)
    return [schemas.RateRead.model_validate(rate) for rate in rates]


@app.get("/rates/latest", response_model=Optional[schemas.RateRead])
async def get_latest_rate(
    session: SessionDep, code: str = Query(..., min_length=1, max_length=20)
):
    """Последняя цена по коду пары"""
    rate = await crud.get_latest_rate(session, code)
    if not rate:
        return None
    return schemas.RateRead.model_validate(rate)


@app.websocket("/ws/items")
async def websocket_items(websocket: WebSocket):
    """WebSocket канал для получения событий"""
    await manager.connect(websocket)
    try:
        await websocket.send_json({"type": "welcome", "payload": "connected"})
        while True:
            message = await websocket.receive_text()
            if message == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception:
        await manager.disconnect(websocket)
        raise


@app.websocket("/ws/tasks")
async def websocket_tasks(websocket: WebSocket):
    """WebSocket алиас для совместимости"""
    await websocket_items(websocket)
