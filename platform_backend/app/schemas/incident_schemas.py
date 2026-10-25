from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class IncidentSeverity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class IncidentStatus(str, Enum):
    open = "open"
    acknowledged = "acknowledged"
    resolved = "resolved"


class IncidentResponse(BaseModel):
    id: UUID
    project_id: UUID
    title: str
    description: str
    severity: IncidentSeverity
    status: IncidentStatus
    first_seen_at: datetime
    last_seen_at: datetime
    created_at: datetime | None = None
    details: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class IncidentStatusUpdate(BaseModel):
    status: IncidentStatus


class IncidentDiagnosisResponse(BaseModel):
    id: UUID
    incident_id: UUID
    summary: str
    possible_causes: list[Any]
    recommendations: list[Any]
    howsolved: str | None = None
    model_name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IncidentDiagnosisUpdate(BaseModel):
    howsolved: str = Field(max_length=10000)


class EvidenceResponse(BaseModel):
    id: UUID
    event_id: UUID
    incident_id: UUID | None
    project_id: UUID
    service_name: str
    environment: str
    sdk_version: str
    request_id: str
    method: str
    route: str
    status_code: int
    duration_ms: float
    exception_type: str | None
    exception_message: str | None
    timestamp: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)