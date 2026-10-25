from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from uuid import UUID


class Project(BaseModel):
    name: str
    description: Optional[str] = None
    github: Optional[str] = None


class ProjectResponse(Project):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectListResponse(BaseModel):
    projects: list[ProjectResponse]


class ApiKeyCreate(BaseModel):
    project_id: UUID


class ApiKeyResponse(BaseModel):
    id: UUID
    key_prefix: str
    is_active: bool
    created_at: datetime
    last_used: Optional[datetime] = None
    project_id: UUID

    model_config = ConfigDict(from_attributes=True)