import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class EventResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    incident_id: uuid.UUID | None
    event_type: str
    service_name: str
    trace_id: str | None
    timestamp: datetime
    payload: dict
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)