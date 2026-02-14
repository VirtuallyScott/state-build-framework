"""
API endpoints for managing Cloud Providers.
"""
from typing import List
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models
from ..dependencies import get_db
from datetime import datetime

router = APIRouter()

@router.post("/cloud_providers/", response_model=models.CloudProviderResponse, status_code=201)
def create_cloud_provider(cloud_provider: models.CloudProviderCreate, db: Session = Depends(get_db)):
    db_cloud_provider = models.CloudProvider(**cloud_provider.dict())
    db.add(db_cloud_provider)
    db.commit()
    db.refresh(db_cloud_provider)
    return db_cloud_provider

@router.get("/cloud_providers/", response_model=List[models.CloudProviderResponse])
def read_cloud_providers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    cloud_providers = db.query(models.CloudProvider).filter(models.CloudProvider.end_date == None).offset(skip).limit(limit).all()
    return cloud_providers

@router.get("/cloud_providers/{cloud_provider_id}", response_model=models.CloudProviderResponse)
def read_cloud_provider(cloud_provider_id: uuid.UUID, db: Session = Depends(get_db)):
    db_cloud_provider = db.query(models.CloudProvider).filter(models.CloudProvider.id == cloud_provider_id).first()
    if db_cloud_provider is None or db_cloud_provider.end_date is not None:
        raise HTTPException(status_code=404, detail="Cloud Provider not found")
    return db_cloud_provider

@router.put("/cloud_providers/{cloud_provider_id}", response_model=models.CloudProviderResponse)
def update_cloud_provider(cloud_provider_id: uuid.UUID, cloud_provider: models.CloudProviderUpdate, db: Session = Depends(get_db)):
    db_cloud_provider = db.query(models.CloudProvider).filter(models.CloudProvider.id == cloud_provider_id).first()
    if db_cloud_provider is None or db_cloud_provider.end_date is not None:
        raise HTTPException(status_code=404, detail="Cloud Provider not found")
    
    for key, value in cloud_provider.dict(exclude_unset=True).items():
        setattr(db_cloud_provider, key, value)
    
    db.commit()
    db.refresh(db_cloud_provider)
    return db_cloud_provider

@router.delete("/cloud_providers/{cloud_provider_id}", status_code=204)
def delete_cloud_provider(cloud_provider_id: uuid.UUID, db: Session = Depends(get_db)):
    db_cloud_provider = db.query(models.CloudProvider).filter(models.CloudProvider.id == cloud_provider_id).first()
    if db_cloud_provider is None or db_cloud_provider.end_date is not None:
        raise HTTPException(status_code=404, detail="Cloud Provider not found")
    
    db_cloud_provider.end_date = datetime.utcnow()
    db.commit()
    return
