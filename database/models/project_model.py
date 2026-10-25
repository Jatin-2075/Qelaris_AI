import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database.database import Base

class ProjectData(Base):
    __tablename__ = "project_data"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(500))
    github : Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc))

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("auth_users.id", ondelete="CASCADE"), index=True)

    owner: Mapped["AuthUser"] = relationship(back_populates="projects")
    api_keys: Mapped[list["ApiKey"]] = relationship(back_populates="project",cascade="all, delete-orphan",)
    metrics: Mapped[list["Metric"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    incidents: Mapped[list["Incident"]] = relationship(back_populates="project", cascade="all, delete-orphan")


class ApiKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    key_hash: Mapped[str] = mapped_column(String(64), unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    last_used: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("project_data.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("auth_users.id", ondelete="CASCADE"), index=True)

    user: Mapped["AuthUser"] = relationship(back_populates="api_keys")
    project: Mapped["ProjectData"] = relationship(back_populates="api_keys")