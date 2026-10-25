import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    String, Float, DateTime, ForeignKey, Index,
    BigInteger, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..DataBase import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Event(Base):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True, nullable=False, index=True)

    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("project_data.id", ondelete="CASCADE"), nullable=False)
    incident_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True, index=True)

    service_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    environment: Mapped[str] = mapped_column(String(50), nullable=False)
    sdk_version: Mapped[str] = mapped_column(String(30), nullable=False)
    request_id: Mapped[str] = mapped_column(String(64), nullable=False)

    method: Mapped[str] = mapped_column(String(10), nullable=False)
    route: Mapped[str] = mapped_column(String(255), nullable=False)
    status_code: Mapped[int] = mapped_column(nullable=False)
    duration_ms: Mapped[float] = mapped_column(Float, nullable=False)

    exception_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    exception_message: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    processing_status: Mapped[str] = mapped_column(String(20), default="pending", index=True, nullable=False)

    project: Mapped["ProjectData"] = relationship(back_populates="events")
    incident: Mapped["Incident | None"] = relationship(back_populates="events")

    __table_args__ = (Index("ix_events_project_timestamp", "project_id", "timestamp"),)
