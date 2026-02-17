"""
API endpoints for managing Image Variants.
"""
from typing import List
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models
from ..dependencies import get_db
from datetime import datetime

router = APIRouter()

@router.post("/image_variants/", response_model=models.ImageVariantResponse, status_code=201)
def create_image_variant(image_variant: models.ImageVariantCreate, db: Session = Depends(get_db)):
    db_image_variant = models.ImageVariant(**image_variant.dict())
    db.add(db_image_variant)
    db.commit()
    db.refresh(db_image_variant)
    return db_image_variant

@router.get("/image_variants/", response_model=List[models.ImageVariantResponse])
def read_image_variants(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    image_variants = db.query(models.ImageVariant).filter(models.ImageVariant.end_date == None).offset(skip).limit(limit).all()
    return image_variants

@router.get("/image_variants/{image_variant_id}", response_model=models.ImageVariantResponse)
def read_image_variant(image_variant_id: uuid.UUID, db: Session = Depends(get_db)):
    db_image_variant = db.query(models.ImageVariant).filter(models.ImageVariant.id == image_variant_id).first()
    if db_image_variant is None or db_image_variant.end_date is not None:
        raise HTTPException(status_code=404, detail="Image Variant not found")
    return db_image_variant

@router.put("/image_variants/{image_variant_id}", response_model=models.ImageVariantResponse)
def update_image_variant(image_variant_id: uuid.UUID, image_variant: models.ImageVariantUpdate, db: Session = Depends(get_db)):
    db_image_variant = db.query(models.ImageVariant).filter(models.ImageVariant.id == image_variant_id).first()
    if db_image_variant is None or db_image_variant.end_date is not None:
        raise HTTPException(status_code=404, detail="Image Variant not found")
    
    for key, value in image_variant.dict(exclude_unset=True).items():
        setattr(db_image_variant, key, value)
    
    db.commit()
    db.refresh(db_image_variant)
    return db_image_variant

@router.delete("/image_variants/{image_variant_id}", status_code=204)
def delete_image_variant(image_variant_id: uuid.UUID, db: Session = Depends(get_db)):
    db_image_variant = db.query(models.ImageVariant).filter(models.ImageVariant.id == image_variant_id).first()
    if db_image_variant is None or db_image_variant.end_date is not None:
        raise HTTPException(status_code=404, detail="Image Variant not found")
    
    db_image_variant.end_date = datetime.utcnow()
    db.commit()
    return
