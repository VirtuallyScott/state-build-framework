"""
API endpoints for managing OS distributions.
"""
from typing import List
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models
from ..dependencies import get_db
from datetime import datetime

router = APIRouter()

@router.post("/os_distributions/", response_model=models.OSDistributionResponse, status_code=201)
def create_os_distribution(os_distribution: models.OSDistributionCreate, db: Session = Depends(get_db)):
    db_os_distribution = models.OSDistribution(**os_distribution.dict())
    db.add(db_os_distribution)
    db.commit()
    db.refresh(db_os_distribution)
    return db_os_distribution

@router.get("/os_distributions/", response_model=List[models.OSDistributionResponse])
def read_os_distributions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    os_distributions = db.query(models.OSDistribution).filter(models.OSDistribution.end_date == None).offset(skip).limit(limit).all()
    return os_distributions

@router.get("/os_distributions/{os_distribution_id}", response_model=models.OSDistributionResponse)
def read_os_distribution(os_distribution_id: uuid.UUID, db: Session = Depends(get_db)):
    db_os_distribution = db.query(models.OSDistribution).filter(models.OSDistribution.id == os_distribution_id).first()
    if db_os_distribution is None or db_os_distribution.end_date is not None:
        raise HTTPException(status_code=404, detail="OS Distribution not found")
    return db_os_distribution

@router.put("/os_distributions/{os_distribution_id}", response_model=models.OSDistributionResponse)
def update_os_distribution(os_distribution_id: uuid.UUID, os_distribution: models.OSDistributionUpdate, db: Session = Depends(get_db)):
    db_os_distribution = db.query(models.OSDistribution).filter(models.OSDistribution.id == os_distribution_id).first()
    if db_os_distribution is None or db_os_distribution.end_date is not None:
        raise HTTPException(status_code=404, detail="OS Distribution not found")
    
    for key, value in os_distribution.dict(exclude_unset=True).items():
        setattr(db_os_distribution, key, value)
    
    db.commit()
    db.refresh(db_os_distribution)
    return db_os_distribution

@router.delete("/os_distributions/{os_distribution_id}", status_code=204)
def delete_os_distribution(os_distribution_id: uuid.UUID, db: Session = Depends(get_db)):
    db_os_distribution = db.query(models.OSDistribution).filter(models.OSDistribution.id == os_distribution_id).first()
    if db_os_distribution is None or db_os_distribution.end_date is not None:
        raise HTTPException(status_code=404, detail="OS Distribution not found")
    
    db_os_distribution.end_date = datetime.utcnow()
    db.commit()
    return
