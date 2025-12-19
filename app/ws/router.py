from fastapi import APIRouter, WebSocket

router = APIRouter()


@router.websocket("/ws/items")
async def websocket_items(websocket: WebSocket):
    await websocket.app.state.manager.serve(websocket)


@router.websocket("/ws/tasks")
async def websocket_tasks(websocket: WebSocket):
    await websocket.app.state.manager.serve(websocket)
