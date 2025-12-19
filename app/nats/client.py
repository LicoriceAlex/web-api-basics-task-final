import json
import os
from typing import Any, Awaitable, Callable, Optional
from uuid import uuid4

try:
    from nats.aio.client import Client as NATS
except Exception:
    NATS = None

EventHandler = Callable[[dict], Awaitable[None]]


class NatsClient:
    """Простой NATS-клиент"""

    def __init__(self, *, url: Optional[str] = None, subject: str = "items.updates", on_event: EventHandler) -> None:
        self.url = url or os.getenv("NATS_URL", "nats://127.0.0.1:4222")
        self.subject = subject
        self.source_id = uuid4().hex

        self._on_event = on_event
        self._nc = None

    @property
    def is_connected(self) -> bool:
        return self._nc is not None

    async def connect(self) -> None:
        if self._nc is not None:
            return

        if NATS is None:
            raise RuntimeError("NATS client is not installed (nats-py)")

        nc = NATS()
        await nc.connect(servers=[self.url], connect_timeout=1)
        await nc.subscribe(self.subject, cb=self._handle_msg)
        self._nc = nc

    async def close(self) -> None:
        if not self._nc:
            return
        try:
            await self._nc.close()
        finally:
            self._nc = None

    async def emit(self, event_type: str, payload: Any = None) -> dict:
        event = {"type": event_type, "payload": payload}
        await self.publish(event)
        return event

    async def publish(self, event: dict) -> None:
        if not self._nc:
            return

        meta = event.get("meta")
        if not isinstance(meta, dict):
            meta = {}
        meta.setdefault("source", self.source_id)
        event["meta"] = meta

        payload = json.dumps(event, default=str).encode("utf-8")
        await self._nc.publish(self.subject, payload)

    async def _handle_msg(self, msg) -> None:
        try:
            event = json.loads(msg.data.decode("utf-8"))
            if not isinstance(event, dict):
                return
            await self._on_event(event)
        except Exception:
            return
