from fastapi import APIRouter, HTTPException, Request

from ..models.schemas import NatsPublishRequest, NatsStatusRead

router = APIRouter(tags=["nats"])


@router.get("/nats/status", response_model=NatsStatusRead)
async def nats_status(request: Request):
    nats = request.app.state.nats
    return {
        "connected": nats.is_connected,
        "url": nats.url,
        "subject": nats.subject,
        "source_id": nats.source_id,
    }


@router.post("/nats/publish")
async def nats_publish(request: Request, payload: NatsPublishRequest):
    nats = request.app.state.nats
    if not nats.is_connected:
        raise HTTPException(status_code=503, detail="NATS is not connected")

    event = await nats.emit(payload.type, payload.payload)
    return {"published": True, "event": event}
