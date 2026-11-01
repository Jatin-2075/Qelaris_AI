from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TelemetryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: UUID
    api: str = Field(min_length=10)
    timestamp: datetime
    service_name: str = Field(min_length=1, max_length=100)
    environment: str = Field(min_length=1, max_length=50)
    sdk_version: str = Field(min_length=1, max_length=30)
    request_id: str = Field(min_length=1, max_length=64)

    method: str = Field(min_length=1, max_length=10)
    route: str = Field(min_length=1, max_length=255)
    status_code: int = Field(ge=100, le=599)
    duration_ms: float = Field(ge=0)

    exception_type: str | None = Field(default=None, max_length=255)
    exception_message: str | None = Field(default=None, max_length=1000)