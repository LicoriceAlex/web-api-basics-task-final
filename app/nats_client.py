import json
import os
import logging
import asyncio
import contextlib
from typing import Awaitable, Callable, Optional
from urllib.parse import urlparse
from uuid import uuid4


EventHandler = Callable[[dict], Awaitable[None]]

logger = logging.getLogger("currency_tracker.nats")


class NatsClient:
    """Обертка над библиотекой nats py"""
    def __init__(
        self,
        *,
        url: Optional[str] = None,
        subject: str = "items.updates",
        on_event: Optional[EventHandler] = None,
    ) -> None:
        self._url = url or os.getenv("NATS_URL", "nats://127.0.0.1:4222")
        self._subject = subject
        self._on_event = on_event
        self._nc = None
        self._source_id = uuid4().hex

    @property
    def source_id(self) -> str:
        """Уникальный id текущего приложения"""
        return self._source_id

    def set_on_event(self, handler: Optional[EventHandler]) -> None:
        """Установить обработчик входящих событий"""
        self._on_event = handler

    @property
    def is_connected(self) -> bool:
        """Показывает есть ли подключение к NATS"""
        return self._nc is not None

    async def connect(self, *, required: bool = False) -> bool:
        """Подключиться к NATS если required True то без NATS будет ошибка"""
        try:
            from nats.aio.client import Client as NATS  # type: ignore
        except Exception as err:
            if required:
                raise RuntimeError(f"NATS client is not installed: {err}")
            return False

        host, port = self._get_host_port(self._url)
        if not await self._is_port_open(host, port):
            message = f"NATS is not running at {self._url}"
            if required:
                raise RuntimeError(message)
            logger.warning(message)
            return False

        async def _error_cb(err: Exception) -> None:
            logger.warning("NATS error: %s: %s", type(err).__name__, err)

        try:
            nc = NATS()
            await nc.connect(
                servers=[self._url],
                connect_timeout=1,
                error_cb=_error_cb,
            )
        except Exception as err:
            message = f"NATS is not available ({self._url}): {type(err).__name__}: {err}"
            if required:
                raise RuntimeError(message)
            logger.warning(message)
            return False

        self._nc = nc

        if self._on_event:
            await self._nc.subscribe(self._subject, cb=self._handle_msg)

        return True

    @staticmethod
    def _get_host_port(url: str) -> tuple[str, int]:
        parsed = urlparse(url)
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or 4222
        return host, port

    @staticmethod
    async def _is_port_open(host: str, port: int) -> bool:
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=0.3,
            )
            writer.close()
            with contextlib.suppress(Exception):
                await writer.wait_closed()
            return True
        except Exception:
            return False

    async def close(self) -> None:
        """Закрыть подключение"""
        if not self._nc:
            return
        try:
            await self._nc.close()
        finally:
            self._nc = None

    async def publish(self, event: dict) -> None:
        """Опубликовать событие в NATS"""
        if not self._nc:
            return

        meta = event.get("meta") if isinstance(event, dict) else None
        if not isinstance(meta, dict):
            meta = {}
        meta.setdefault("source", self._source_id)
        event["meta"] = meta

        try:
            payload = json.dumps(event, default=str).encode("utf-8")
            await self._nc.publish(self._subject, payload)
        except Exception:
            return

    async def _handle_msg(self, msg) -> None:
        """Внутренний обработчик сообщений из подписки"""
        if not self._on_event:
            return

        try:
            raw = msg.data.decode("utf-8")
            event = json.loads(raw)
            if not isinstance(event, dict):
                return

            await self._on_event(event)
        except Exception:
            return
