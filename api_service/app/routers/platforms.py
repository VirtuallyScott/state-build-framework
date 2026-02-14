"""
API endpoints for managing platforms.
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

@router.post("/platforms/", response_model=models.PlatformResponse, status_code=201)
def create_platform(
    platform: models.PlatformCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_write)
):
    """Create a new platform. Requires write permission."""
    db_platform = models.Platform(**platform.dict())
    db.add(db_platform)
    db.commit()
    db.refresh(db_platform)
    return db_platform

@router.get("/platforms/", response_model=List[models.PlatformResponse])
def read_platforms(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user_or_api_key)
):
    """List all platforms. Requires authentication."""
    platforms = db.query(models.Platform).filter(
        models.Platform.deactivated_at == None
    ).offset(skip).limit(limit).all()
    return platforms

@router.get("/platforms/{platform_id}", response_model=models.PlatformResponse)
def read_platform(
    platform_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user_or_api_key)
):
    """Get a specific platform. Requires authentication."""
    db_platform = db.query(models.Platform).filter(
        models.Platform.id == platform_id,
        models.Platform.deactivated_at == None
    ).first()
    if db_platform is None:
        raise HTTPException(status_code=404, detail="Platform not found")
    return db_platform


@router.put("/platforms/{platform_id}", response_model=models.PlatformResponse)
def update_platform(
    platform_id: str,
    platform: models.PlatformUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_write)
):
    """Update a platform. Requires write permission."""
    db_platform = db.query(models.Platform).filter(
        models.Platform.id == platform_id,
        models.Platform.deactivated_at == None
    ).first()
    if db_platform is None:
        raise HTTPException(status_code=404, detail="Platform not found")
    
    for key, value in platform.dict(exclude_unset=True).items():
        setattr(db_platform, key, value)
    
    db.commit()
    db.refresh(db_platform)
    return db_platform


@router.delete("/platforms/{platform_id}", status_code=204)
def delete_platform(
    platform_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    """Soft delete a platform by setting deactivated_at. Requires admin permission."""
    db_platform = db.query(models.Platform).filter(
        models.Platform.id == platform_id,
        models.Platform.deactivated_at == None
    ).first()
    if db_platform is None:
        raise HTTPException(status_code=404, detail="Platform not found")
    
    db_platform.deactivated_at = datetime.utcnow()
    db.commit()
    return
