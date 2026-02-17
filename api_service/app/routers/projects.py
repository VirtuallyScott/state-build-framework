"""
Projects API router.
"""
from typing import List
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models
from ..dependencies import get_db
from ..core.auth import get_current_user_or_api_key, require_write, require_admin
from datetime import datetime

router = APIRouter()


@router.post("/projects/", response_model=models.ProjectResponse, status_code=201)
def create_project(
    project: models.ProjectCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_write)
):
    """Create a new project. Requires write permission."""
    db_project = models.Project(**project.dict())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


@router.get("/projects/", response_model=List[models.ProjectResponse])
def read_projects(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user_or_api_key)
):
    """List all projects. Requires authentication."""
    projects = db.query(models.Project).offset(skip).limit(limit).all()
    return projects


@router.get("/projects/{project_id}", response_model=models.ProjectResponse)
def read_project(
    project_id: uuid.UUID, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user_or_api_key)
):
    """Get a specific project. Requires authentication."""
    db_project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return db_project


@router.put("/projects/{project_id}", response_model=models.ProjectResponse)
def update_project(
    project_id: uuid.UUID, 
    project: models.ProjectUpdate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_write)
):
    """Update a project. Requires write permission."""
    db_project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    
    for key, value in project.dict(exclude_unset=True).items():
        setattr(db_project, key, value)
    
    db.commit()
    db.refresh(db_project)
    return db_project


@router.delete("/projects/{project_id}", status_code=204)
def delete_project(
    project_id: uuid.UUID, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    """Delete a project. Requires admin permission."""
    db_project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Soft delete by setting end_date
    if not db_project.end_date:
        db_project.end_date = datetime.utcnow()
        db.commit()
    
    return


    


