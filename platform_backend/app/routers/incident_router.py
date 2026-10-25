from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database.database import get_db
from database.models.event_model import Event
from database.models.incident_model import Incident, IncidentDiagnosis
from database.models.project_model import ProjectData
from platform_backend.app.security.security import get_current_user
from platform_backend.app.schemas.incident_schemas import (
    EvidenceResponse,
    IncidentDiagnosisResponse,
    IncidentDiagnosisUpdate,
    IncidentResponse,
    IncidentStatus,
    IncidentStatusUpdate,
)


router = APIRouter(prefix="/projects/{project_id}/incidents", tags=["Incidents"])


def _get_owned_project(
    project_id: UUID,
    db: Session,
    current_user,
) -> ProjectData:
    project = (
        db.query(ProjectData)
        .filter(
            ProjectData.id == project_id,
            ProjectData.user_id == current_user.id,
        )
        .first()
    )
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


def _get_owned_incident(
    project_id: UUID,
    incident_id: UUID,
    db: Session,
    current_user,
) -> Incident:
    _get_owned_project(project_id, db, current_user)
    incident = (
        db.query(Incident)
        .filter(Incident.id == incident_id, Incident.project_id == project_id)
        .first()
    )
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return incident


@router.get("", response_model=list[IncidentResponse])
def list_incidents(
    project_id: UUID,
    status_filter: IncidentStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _get_owned_project(project_id, db, current_user)
    query = db.query(Incident).filter(Incident.project_id == project_id)
    if status_filter is not None:
        query = query.filter(Incident.status == status_filter.value)
    return query.order_by(Incident.last_seen_at.desc()).limit(limit).all()


@router.get("/{incident_id}", response_model=IncidentResponse)
def get_incident(
    project_id: UUID,
    incident_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return _get_owned_incident(project_id, incident_id, db, current_user)


@router.get("/{incident_id}/evidence", response_model=list[EvidenceResponse])
def list_incident_evidence(
    project_id: UUID,
    incident_id: UUID,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _get_owned_incident(project_id, incident_id, db, current_user)
    return (
        db.query(Event)
        .filter(Event.project_id == project_id, Event.incident_id == incident_id)
        .order_by(Event.timestamp.desc())
        .limit(limit)
        .all()
    )


@router.get("/{incident_id}/diagnosis", response_model=IncidentDiagnosisResponse)
def get_incident_diagnosis(
    project_id: UUID,
    incident_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    incident = _get_owned_incident(project_id, incident_id, db, current_user)
    diagnosis = (
        db.query(IncidentDiagnosis)
        .filter(IncidentDiagnosis.incident_id == incident.id)
        .order_by(IncidentDiagnosis.created_at.desc())
        .first()
    )
    if diagnosis is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident diagnosis not found")
    return diagnosis


@router.patch("/{incident_id}/diagnosis", response_model=IncidentDiagnosisResponse)
def update_incident_diagnosis(
    project_id: UUID,
    incident_id: UUID,
    payload: IncidentDiagnosisUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    incident = _get_owned_incident(project_id, incident_id, db, current_user)
    diagnosis = (
        db.query(IncidentDiagnosis)
        .filter(IncidentDiagnosis.incident_id == incident.id)
        .order_by(IncidentDiagnosis.created_at.desc())
        .first()
    )
    if diagnosis is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident diagnosis not found")
    diagnosis.howsolved = payload.howsolved
    db.commit()
    db.refresh(diagnosis)
    return diagnosis


@router.patch("/{incident_id}/status", response_model=IncidentResponse)
def update_incident_status(
    project_id: UUID,
    incident_id: UUID,
    payload: IncidentStatusUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    incident = _get_owned_incident(project_id, incident_id, db, current_user)
    incident.status = payload.status.value
    db.commit()
    db.refresh(incident)
    return incident