from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter(include_in_schema=False)


@router.get("/")
async def ui():
    html_path = Path(__file__).resolve().parent.parent / "static" / "index.html"
    return FileResponse(html_path, media_type="text/html")


@router.get("/ui")
async def ui_alias():
    return await ui()


@router.get("/ws-ui")
async def ws_ui():
    html_path = Path(__file__).resolve().parent.parent / "static" / "ws.html"
    return FileResponse(html_path, media_type="text/html")

