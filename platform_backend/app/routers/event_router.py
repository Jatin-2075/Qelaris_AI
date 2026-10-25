from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import tuple_
from sqlalchemy.orm import Session

from ..database.database import get_db
from ..models.project_model import ProjectData
from ..models.event_model import Event, Incident
from ..security.security import get_current_user

router = APIRouter(tags=["Project Monitoring"])

class ConnectionManager:
    def __init__(self):
        self.connections: dict[str, list[WebSocket]] = {}

    async def connect(self, project_id: str, websocket: WebSocket):
        await websocket.accept()
        self.connections.setdefault(project_id, []).append(websocket)

    def disconnect(self, project_id: str, websocket: WebSocket):
        clients = self.connections.get(project_id, [])
        if websocket in clients:
            clients.remove(websocket)
        if not clients:
            self.connections.pop(project_id, None)

    async def broadcast(self, project_id: str, data: dict):
        for ws in self.connections.get(project_id, []).copy():
            try:
                await ws.send_json(data)
            except Exception:
                self.disconnect(project_id, ws)


manager = ConnectionManager()

def verify_project_access(project_id: UUID, db: Session, user_id: UUID):
    project = db.query(ProjectData.id).filter(
        ProjectData.id == project_id,
        ProjectData.owner_id == user_id,
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

@router.websocket("/ws/projects/{project_id}")
async def project_websocket(
    websocket: WebSocket,
    project_id: UUID,
    token: str,
    db: Session = Depends(get_db),
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            await websocket.close(code=1008)
            return
        user_id = UUID(payload["sub"])
    except (JWTError, ValueError, KeyError, TypeError):
        await websocket.close(code=1008)
        return

    try:
        verify_project_access(project_id, db, user_id)
    except HTTPException:
        await websocket.close(code=1008)
        return
    finally:
        db.close()

    project_key = str(project_id)
    await manager.connect(project_key, websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(project_key, websocket)
    except Exception:
        manager.disconnect(project_key, websocket)


@router.get("/projects/{project_id}/events")
def get_events(
    project_id: UUID,
    limit: int = Query(50, ge=1, le=100),
    cursor_timestamp: datetime | None = None,
    cursor_id: UUID | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if (cursor_timestamp is None) != (cursor_id is None):
        raise HTTPException(
            status_code=400,
            detail="Provide both cursor_timestamp and cursor_id",
        )

    verify_project_access(project_id, db, current_user.id)

    query = db.query(Event).filter(Event.project_id == project_id)

    if cursor_timestamp is not None:
        query = query.filter(
            tuple_(Event.timestamp, Event.id)
            < tuple_(cursor_timestamp, cursor_id)
        )

    rows = query.order_by(
        Event.timestamp.desc(), Event.id.desc()
    ).limit(limit + 1).all()

    has_more = len(rows) > limit
    rows = rows[:limit]
    next_cursor = None

    if has_more and rows:
        last = rows[-1]
        next_cursor = {
            "cursor_timestamp": last.timestamp.isoformat(),
            "cursor_id": str(last.id),
        }

    return {
        "items": [
            {
                "id": str(e.id),
                "project_id": str(e.project_id),
                "incident_id": str(e.incident_id) if e.incident_id else None,
                "event_type": e.event_type,
                "service_name": e.service_name,
                "trace_id": e.trace_id,
                "timestamp": e.timestamp.isoformat(),
                "payload": e.payload,
                "created_at": e.created_at.isoformat(),
            }
            for e in rows
        ],
        "next_cursor": next_cursor,
        "has_more": has_more,
    }


@router.get("/projects/{project_id}/incidents")
def get_incidents(
    project_id: UUID,
    limit: int = Query(50, ge=1, le=100),
    cursor_timestamp: datetime | None = None,
    cursor_id: UUID | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if (cursor_timestamp is None) != (cursor_id is None):
        raise HTTPException(
            status_code=400,
            detail="Provide both cursor_timestamp and cursor_id",
        )

    verify_project_access(project_id, db, current_user.id)

    query = db.query(Incident).filter(
        Incident.project_id == project_id
    )

    if cursor_timestamp is not None:
        query = query.filter(
            tuple_(Incident.last_seen_at, Incident.id)
            < tuple_(cursor_timestamp, cursor_id)
        )

    rows = query.order_by(
        Incident.last_seen_at.desc(), Incident.id.desc()
    ).limit(limit + 1).all()

    has_more = len(rows) > limit
    rows = rows[:limit]
    next_cursor = None

    if has_more and rows:
        last = rows[-1]
        next_cursor = {
            "cursor_timestamp": last.last_seen_at.isoformat(),
            "cursor_id": str(last.id),
        }

    return {
        "items": [
            {
                "id": str(i.id),
                "project_id": str(i.project_id),
                "title": i.title,
                "description": i.description,
                "severity": i.severity.value,
                "status": i.status.value,
                "first_seen_at": i.first_seen_at.isoformat(),
                "last_seen_at": i.last_seen_at.isoformat(),
            }
            for i in rows
        ],
        "next_cursor": next_cursor,
        "has_more": has_more,
    }


async def notify_event(event: Event):
    await manager.broadcast(str(event.project_id), {
        "type": "event.created",
        "data": {
            "id": str(event.id),
            "event_type": event.event_type,
            "service_name": event.service_name,
            "timestamp": event.timestamp.isoformat(),
        },
    })


async def notify_incident(incident: Incident):
    await manager.broadcast(str(incident.project_id), {
        "type": "incident.updated",
        "data": {
            "id": str(incident.id),
            "title": incident.title,
            "severity": incident.severity.value,
            "status": incident.status.value,
            "last_seen_at": incident.last_seen_at.isoformat(),
        },
    })
