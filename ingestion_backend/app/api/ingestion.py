import uuid
import hashlib
import secrets
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from redis.asyncio import Redis

from ....database.database import get_db
from ....database.models.event_model import Event
from ....database.models.project_model import ApiKey
from ..schemas import TelemetryRequest
from ..setting import settings

hashed = CryptContext(schemes=["bcrypt"], deprecated="auto")
redis = Redis.from_url(settings.REDIS_URL, decode_responses=True) if settings.REDIS_URL else None

router = APIRouter(tags=["save event"])

def get_api_key(api: str, db: Session) -> ApiKey | None:
    key_prefix = api[:10]
    key_hash = hashlib.sha256(api.encode()).hexdigest()

    found = db.query(ApiKey).filter(ApiKey.key_prefix == key_prefix,ApiKey.is_active.is_(True),).first()

    if found and secrets.compare_digest(found.key_hash, key_hash):
        return found

    return None


@router.post("/telemetry", status_code=status.HTTP_202_ACCEPTED)
async def pipeline(payload: TelemetryRequest, db: Session = Depends(get_db)):
    api_key = get_api_key(payload.api, db)
    
    if not api_key: raise HTTPException(status_code=401, detail="Invalid API key")

    event = Event(
        event_id=payload.event_id, 
        project_id=api_key.project_id, 
        service_name=payload.service_name, 
        environment=payload.environment, 
        sdk_version=payload.sdk_version, 
        request_id=payload.request_id, 
        method=payload.method, 
        route=payload.route, 
        status_code=payload.status_code,
        duration_ms=payload.duration_ms,
        exception_type=payload.exception_type, 
        exception_message=payload.exception_message, 
        timestamp=payload.timestamp, 
        processing_status="pending"
        )

    db.add(event)
    db.commit()
    db.refresh(event)

    fresh_event_id = str(event.id)
    project_id = str(event.project_id)

    if redis is None:
        raise HTTPException(status_code=503, detail="Queue is not configured")

    try:
        await redis.xadd(
            "sentinel:events",
            {"project_id": project_id, "event_id": fresh_event_id},
        )
    except Exception:
        raise HTTPException(status_code=503, detail="Event saved, but queue unavailable")

    return {"accepted": True, "event_id": str(event.id), "project_id": str(event.project_id), "processing_status": event.processing_status}