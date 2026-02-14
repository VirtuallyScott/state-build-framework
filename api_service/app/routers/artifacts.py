"""
Build Artifact management endpoints for the Build State API.
Tracks artifacts created during builds (snapshots, images, etc.)
"""
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from sqlalchemy.orm import Session

from .. import models
from ..core.auth import get_current_user_or_api_key, require_write, require_admin
from ..dependencies import get_db

router = APIRouter()


@router.post(
    "/builds/{build_id}/artifacts",
    response_model=models.BuildArtifactResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["artifacts"]
)
def create_artifact(
    build_id: str,
    artifact: models.BuildArtifactCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_write),
):
    """
    Register a new artifact for a build. Requires write permission.
    
    Artifacts represent intermediate or final outputs from build steps
    (VM snapshots, disk images, AMIs, configuration files, etc.)
    """
    # Validate build exists
    db_build = db.query(models.Build).filter(models.Build.id == build_id).first()
    if not db_build:
        raise HTTPException(status_code=404, detail=f"Build {build_id} not found")
    
    # Check if artifact name already exists for this build
    existing = db.query(models.BuildArtifact).filter(
        models.BuildArtifact.build_id == build_id,
        models.BuildArtifact.artifact_name == artifact.artifact_name,
        models.BuildArtifact.deleted_at.is_(None)
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Artifact with name '{artifact.artifact_name}' already exists for this build"
        )
    
    now = datetime.utcnow()
    db_artifact = models.BuildArtifact(
        id=str(uuid.uuid4()),
        build_id=build_id,
        state_code=artifact.state_code,
        artifact_name=artifact.artifact_name,
        artifact_type=artifact.artifact_type,
        artifact_path=artifact.artifact_path,
        storage_backend=artifact.storage_backend,
        storage_region=artifact.storage_region,
        storage_bucket=artifact.storage_bucket,
        storage_key=artifact.storage_key,
        size_bytes=artifact.size_bytes,
        checksum=artifact.checksum,
        checksum_algorithm=artifact.checksum_algorithm,
        is_resumable=artifact.is_resumable,
        is_final=artifact.is_final,
        expires_at=artifact.expires_at,
        metadata=artifact.metadata,
        created_at=now,
        updated_at=now
    )
    
    db.add(db_artifact)
    db.commit()
    db.refresh(db_artifact)
    
    return db_artifact


@router.get(
    "/builds/{build_id}/artifacts",
    response_model=List[models.BuildArtifactResponse],
    tags=["artifacts"]
)
def list_artifacts(
    build_id: str,
    state_code: Optional[int] = Query(None, description="Filter by state code"),
    artifact_type: Optional[str] = Query(None, description="Filter by artifact type"),
    is_resumable: Optional[bool] = Query(None, description="Filter by resumable flag"),
    is_final: Optional[bool] = Query(None, description="Filter by final flag"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user_or_api_key),
):
    """
    List all artifacts for a build with optional filters.
    """
    # Validate build exists
    db_build = db.query(models.Build).filter(models.Build.id == build_id).first()
    if not db_build:
        raise HTTPException(status_code=404, detail=f"Build {build_id} not found")
    
    query = db.query(models.BuildArtifact).filter(
        models.BuildArtifact.build_id == build_id,
        models.BuildArtifact.deleted_at.is_(None)
    )
    
    if state_code is not None:
        query = query.filter(models.BuildArtifact.state_code == state_code)
    
    if artifact_type:
        query = query.filter(models.BuildArtifact.artifact_type == artifact_type)
    
    if is_resumable is not None:
        query = query.filter(models.BuildArtifact.is_resumable == is_resumable)
    
    if is_final is not None:
        query = query.filter(models.BuildArtifact.is_final == is_final)
    
    artifacts = query.order_by(models.BuildArtifact.state_code, models.BuildArtifact.created_at).all()
    
    return artifacts


@router.get(
    "/builds/{build_id}/artifacts/{artifact_id}",
    response_model=models.BuildArtifactResponse,
    tags=["artifacts"]
)
def get_artifact(
    build_id: str,
    artifact_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user_or_api_key),
):
    """
    Get details of a specific artifact.
    """
    artifact = db.query(models.BuildArtifact).filter(
        models.BuildArtifact.id == artifact_id,
        models.BuildArtifact.build_id == build_id,
        models.BuildArtifact.deleted_at.is_(None)
    ).first()
    
    if not artifact:
        raise HTTPException(
            status_code=404,
            detail=f"Artifact {artifact_id} not found for build {build_id}"
        )
    
    return artifact


@router.patch(
    "/builds/{build_id}/artifacts/{artifact_id}",
    response_model=models.BuildArtifactResponse,
    tags=["artifacts"]
)
def update_artifact(
    build_id: str,
    artifact_id: str,
    artifact_update: models.BuildArtifactUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_write),
):
    """
    Update artifact metadata. Requires write permission.
    """
    db_artifact = db.query(models.BuildArtifact).filter(
        models.BuildArtifact.id == artifact_id,
        models.BuildArtifact.build_id == build_id,
        models.BuildArtifact.deleted_at.is_(None)
    ).first()
    
    if not db_artifact:
        raise HTTPException(
            status_code=404,
            detail=f"Artifact {artifact_id} not found for build {build_id}"
        )
    
    # Update only provided fields
    update_data = artifact_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_artifact, field, value)
    
    db_artifact.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_artifact)
    
    return db_artifact


@router.delete(
    "/builds/{build_id}/artifacts/{artifact_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["artifacts"]
)
def delete_artifact(
    build_id: str,
    artifact_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin),
):
    """
    Soft delete an artifact. Requires admin permission.
    
    The artifact record is preserved with a deleted_at timestamp for audit purposes.
    The actual artifact file in storage is NOT deleted.
    """
    db_artifact = db.query(models.BuildArtifact).filter(
        models.BuildArtifact.id == artifact_id,
        models.BuildArtifact.build_id == build_id,
        models.BuildArtifact.deleted_at.is_(None)
    ).first()
    
    if not db_artifact:
        raise HTTPException(
            status_code=404,
            detail=f"Artifact {artifact_id} not found for build {build_id}"
        )
    
    db_artifact.deleted_at = datetime.utcnow()
    db.commit()
    
    return None
