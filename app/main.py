from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.router import router as api_router
from .config import settings
from .db.database import SessionLocal, init_db
from .nats.client import NatsClient
from .tasks.rates_updater import RatesUpdater
from .ws.manager import ConnectionManager
from .ws.router import router as ws_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Трекер цен криптовалют",
        description="REST API + WebSocket + фоновая задача + NATS + SQLite",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.state.manager = ConnectionManager()
    app.state.nats = NatsClient(
        url=settings.nats_url,
        subject=settings.nats_subject,
        on_event=app.state.manager.broadcast,
    )
    app.state.rates_updater = RatesUpdater(
        SessionLocal,
        notifier=app.state.nats.publish,
        interval_seconds=settings.rates_interval_seconds,
        source_url=settings.rates_source_url,
    )

    app.include_router(api_router)
    app.include_router(ws_router)

    @app.on_event("startup")
    async def on_startup() -> None:
        await init_db()
        await app.state.nats.connect()
        await app.state.rates_updater.start()

    @app.on_event("shutdown")
    async def on_shutdown() -> None:
        await app.state.rates_updater.stop()
        await app.state.nats.close()

    return app


app = create_app()
