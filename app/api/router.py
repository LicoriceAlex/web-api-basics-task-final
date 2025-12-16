from fastapi import APIRouter

from .items import router as items_router
from .nats_api import router as nats_router
from .rates import router as rates_router
from .tasks import router as tasks_router
from .ui import router as ui_router

router = APIRouter()
router.include_router(ui_router)
router.include_router(items_router)
router.include_router(tasks_router)
router.include_router(rates_router)
router.include_router(nats_router)