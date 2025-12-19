from typing import Iterable

from fastapi import WebSocket
from fastapi.encoders import jsonable_encoder
from fastapi.websockets import WebSocketDisconnect
from starlette.websockets import WebSocketState


class ConnectionManager:
    """Хранит активные WebSocket соединения"""

    def __init__(self) -> None:
        """Создает менеджер подключений"""
        self._connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        """Принимает подключение и сохраняет его"""
        await websocket.accept()
        self._connections.add(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        """Удаляет подключение из списка"""
        self._connections.discard(websocket)

    async def serve(self, websocket: WebSocket) -> None:
        await self.connect(websocket)
        try:
            await websocket.send_json({"type": "welcome", "payload": "connected"})
            while True:
                message = await websocket.receive_text()
                if message == "ping":
                    await websocket.send_json({"type": "pong"})
        except WebSocketDisconnect:
            await self.disconnect(websocket)
        except Exception:
            await self.disconnect(websocket)
            raise

    async def broadcast(self, message: dict) -> None:
        """Рассылает сообщение всем активным подключениям"""
        targets: Iterable[WebSocket] = list(self._connections)
        serializable = jsonable_encoder(message)

        for ws in targets:
            if ws.application_state != WebSocketState.CONNECTED:
                await self.disconnect(ws)
                continue
            try:
                await ws.send_json(serializable)
            except Exception:
                await self.disconnect(ws)
