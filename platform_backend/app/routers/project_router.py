
import secrets
import hashlib
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database.database import get_db
from ..models.project_model import ProjectData, ApiKey
from ..schemas.project_schema import Project, ProjectResponse, ApiKeyCreate, ApiKeyResponse
from ..security.security import get_current_user

router = APIRouter(tags=["Projects & API Keys"])

@router.post("/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(payload: Project, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    project = ProjectData(name=payload.name, description=payload.description, github=payload.github, owner_id=current_user.id)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/projects", response_model=list[ProjectResponse])
def get_projects(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return db.query(ProjectData).filter(ProjectData.owner_id == current_user.id).all()


@router.get("/projects/{project_id}", response_model=ProjectResponse)
def get_project(project_id: UUID, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    project = db.query(ProjectData).filter(ProjectData.id == project_id, ProjectData.owner_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: UUID, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    project = db.query(ProjectData).filter(ProjectData.id == project_id, ProjectData.owner_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()


@router.post("/api-keys", status_code=status.HTTP_201_CREATED)
def create_api_key(payload: ApiKeyCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    project = db.query(ProjectData).filter(ProjectData.id == payload.project_id, ProjectData.owner_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    raw_key = "rp_" + secrets.token_urlsafe(32)
    api_key = ApiKey(
        project_id=project.id,
        user_id=current_user.id,
        key_prefix=raw_key[:10],
        key_hash=hashlib.sha256(raw_key.encode()).hexdigest(),
        is_active=True
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)

    return {"key": raw_key, "api_key": ApiKeyResponse.model_validate(api_key)}


@router.get("/api-keys", response_model=list[ApiKeyResponse])
def get_api_keys(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return db.query(ApiKey).filter(ApiKey.user_id == current_user.id).all()


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_api_key(key_id: UUID, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    api_key = db.query(ApiKey).filter(ApiKey.id == key_id, ApiKey.user_id == current_user.id).first()
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    api_key.is_active = False
    db.commit()
