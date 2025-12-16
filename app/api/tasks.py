from fastapi import APIRouter, Request

router = APIRouter(tags=["tasks"])


@router.post("/tasks/run")
async def run_background_task(request: Request):
    created = await request.app.state.rates_updater.run_once()
    return {
        "created_rates": created,
        "status": {
            "nats_connected": request.app.state.nats.is_connected,
            "rates_updater": request.app.state.rates_updater.status(),
        },
    }


@router.get("/tasks/status")
async def get_tasks_status(request: Request):
    return {
        "nats_connected": request.app.state.nats.is_connected,
        "rates_updater": request.app.state.rates_updater.status(),
    }

