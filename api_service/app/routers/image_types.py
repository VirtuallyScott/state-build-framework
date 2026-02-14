"""
API endpoints for managing image types.
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

@router.post("/image_types/", response_model=models.ImageTypeResponse, status_code=201)
def create_image_type(
    image_type: models.ImageTypeCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_write)
):
    """Create a new image type. Requires write permission."""
    db_image_type = models.ImageType(**image_type.dict())
    db.add(db_image_type)
    db.commit()
    db.refresh(db_image_type)
    return db_image_type

@router.get("/image_types/", response_model=List[models.ImageTypeResponse])
def read_image_types(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user_or_api_key)
):
    """List all image types. Requires authentication."""
    image_types = db.query(models.ImageType).filter(
        models.ImageType.deactivated_at == None
    ).offset(skip).limit(limit).all()
    return image_types

@router.get("/image_types/{image_type_id}", response_model=models.ImageTypeResponse)
def read_image_type(
    image_type_id: str, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user_or_api_key)
):
    """Get a specific image type. Requires authentication."""
    db_image_type = db.query(models.ImageType).filter(
        models.ImageType.id == image_type_id,
        models.ImageType.deactivated_at == None
    ).first()
    if db_image_type is None:
        raise HTTPException(status_code=404, detail="Image type not found")
    return db_image_type


@router.put("/image_types/{image_type_id}", response_model=models.ImageTypeResponse)
def update_image_type(
    image_type_id: str,
    image_type: models.ImageTypeUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_write)
):
    """Update an image type. Requires write permission."""
    db_image_type = db.query(models.ImageType).filter(
        models.ImageType.id == image_type_id,
        models.ImageType.deactivated_at == None
    ).first()
    if db_image_type is None:
        raise HTTPException(status_code=404, detail="Image type not found")
    
    for key, value in image_type.dict(exclude_unset=True).items():
        setattr(db_image_type, key, value)
    
    db.commit()
    db.refresh(db_image_type)
    return db_image_type


@router.delete("/image_types/{image_type_id}", status_code=204)
def delete_image_type(
    image_type_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    """Soft delete an image type by setting deactivated_at. Requires admin permission."""
    db_image_type = db.query(models.ImageType).filter(
        models.ImageType.id == image_type_id,
        models.ImageType.deactivated_at == None
    ).first()
    if db_image_type is None:
        raise HTTPException(status_code=404, detail="Image type not found")
    
    db_image_type.deactivated_at = datetime.utcnow()
    db.commit()
    return
