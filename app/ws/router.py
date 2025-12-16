from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


@router.websocket("/ws/items")
async def websocket_items(websocket: WebSocket):
    manager = websocket.app.state.manager
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


@router.websocket("/ws/tasks")
async def websocket_tasks(websocket: WebSocket):
    await websocket_items(websocket)

