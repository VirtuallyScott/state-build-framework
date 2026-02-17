"""
API endpoints for managing OS versions.
"""
from typing import List
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models
from ..dependencies import get_db
from ..core.auth import get_current_user_or_api_key, require_write, require_admin

router = APIRouter()

@router.post("/os_versions/", response_model=models.OSVersionResponse, status_code=201)
def create_os_version(
    os_version: models.OSVersionCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_write)
):
    """Create a new OS version. Requires write permission."""
    db_os_version = models.OSVersion(**os_version.dict())
    db.add(db_os_version)
    db.commit()
    db.refresh(db_os_version)
    return db_os_version

@router.get("/os_versions/", response_model=List[models.OSVersionResponse])
def read_os_versions(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user_or_api_key)
):
    """List all OS versions. Requires authentication."""
    os_versions = db.query(models.OSVersion).filter(
        models.OSVersion.deactivated_at == None
    ).offset(skip).limit(limit).all()
    return os_versions

@router.get("/os_versions/{os_version_id}", response_model=models.OSVersionResponse)
def read_os_version(
    os_version_id: str, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user_or_api_key)
):
    """Get a specific OS version. Requires authentication."""
    db_os_version = db.query(models.OSVersion).filter(
        models.OSVersion.id == os_version_id,
        models.OSVersion.deactivated_at == None
    ).first()
    if db_os_version is None:
        raise HTTPException(status_code=404, detail="OS version not found")
    return db_os_version


@router.put("/os_versions/{os_version_id}", response_model=models.OSVersionResponse)
def update_os_version(
    os_version_id: str,
    os_version: models.OSVersionUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_write)
):
    """Update an OS version. Requires write permission."""
    db_os_version = db.query(models.OSVersion).filter(
        models.OSVersion.id == os_version_id,
        models.OSVersion.deactivated_at == None
    ).first()
    if db_os_version is None:
        raise HTTPException(status_code=404, detail="OS version not found")
    
    for key, value in os_version.dict(exclude_unset=True).items():
        setattr(db_os_version, key, value)
    
    db.commit()
    db.refresh(db_os_version)
    return db_os_version


@router.delete("/os_versions/{os_version_id}", status_code=204)
def delete_os_version(
    os_version_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    """Soft delete an OS version by setting deactivated_at. Requires admin permission."""
    db_os_version = db.query(models.OSVersion).filter(
        models.OSVersion.id == os_version_id,
        models.OSVersion.deactivated_at == None
    ).first()
    if db_os_version is None:
        raise HTTPException(status_code=404, detail="OS version not found")
    
    db_os_version.deactivated_at = datetime.utcnow()
    db.commit()
    return
