"""
Build Resume management endpoints for the Build State API.
Handles resume requests, resumable state configuration, and resume context.
"""
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from .. import models
from ..core.auth import get_current_user_or_api_key, require_write, require_admin
from ..dependencies import get_db

router = APIRouter()


# ============================================================================
# RESUMABLE STATE CONFIGURATION
# ============================================================================

@router.post(
    "/projects/{project_id}/resumable-states",
    response_model=models.ResumableStateResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["resume"]
)
def create_resumable_state(
    project_id: str,
    resumable_state: models.ResumableStateCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_write),
):
    """
    Define which state codes are resumable for a project. Requires write permission.
    
    This configures the resume strategy, required artifacts, and variables needed
    to resume from a specific state code.
    """
    # Validate project exists
    db_project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    
    # Check if already exists
    existing = db.query(models.ResumableState).filter(
        models.ResumableState.project_id == project_id,
        models.ResumableState.state_code == resumable_state.state_code
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Resumable state {resumable_state.state_code} already configured for this project"
        )
    
    now = datetime.utcnow()
    db_resumable = models.ResumableState(
        id=str(uuid.uuid4()),
        project_id=project_id,
        state_code=resumable_state.state_code,
        is_resumable=resumable_state.is_resumable,
        resume_strategy=resumable_state.resume_strategy,
        required_artifacts=resumable_state.required_artifacts,
        required_variables=resumable_state.required_variables,
        resume_command=resumable_state.resume_command,
        resume_timeout_seconds=resumable_state.resume_timeout_seconds,
        description=resumable_state.description,
        notes=resumable_state.notes,
        created_at=now,
        updated_at=now
    )
    
    db.add(db_resumable)
    db.commit()
    db.refresh(db_resumable)
    
    return db_resumable


@router.get(
    "/projects/{project_id}/resumable-states",
    response_model=List[models.ResumableStateResponse],
    tags=["resume"]
)
def list_resumable_states(
    project_id: str,
    is_resumable: Optional[bool] = Query(None, description="Filter by resumable flag"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user_or_api_key),
):
    """
    List all resumable state configurations for a project.
    """
    # Validate project exists
    db_project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    
    query = db.query(models.ResumableState).filter(
        models.ResumableState.project_id == project_id
    )
    
    if is_resumable is not None:
        query = query.filter(models.ResumableState.is_resumable == is_resumable)
    
    states = query.order_by(models.ResumableState.state_code).all()
    
    return states


@router.get(
    "/projects/{project_id}/resumable-states/{state_code}",
    response_model=models.ResumableStateResponse,
    tags=["resume"]
)
def get_resumable_state(
    project_id: str,
    state_code: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user_or_api_key),
):
    """
    Get resumable state configuration for a specific state code.
    """
    resumable = db.query(models.ResumableState).filter(
        models.ResumableState.project_id == project_id,
        models.ResumableState.state_code == state_code
    ).first()
    
    if not resumable:
        raise HTTPException(
            status_code=404,
            detail=f"Resumable state {state_code} not configured for project {project_id}"
        )
    
    return resumable


@router.put(
    "/projects/{project_id}/resumable-states/{state_code}",
    response_model=models.ResumableStateResponse,
    tags=["resume"]
)
def update_resumable_state(
    project_id: str,
    state_code: int,
    resumable_update: models.ResumableStateUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_write),
):
    """
    Update resumable state configuration. Requires write permission.
    """
    db_resumable = db.query(models.ResumableState).filter(
        models.ResumableState.project_id == project_id,
        models.ResumableState.state_code == state_code
    ).first()
    
    if not db_resumable:
        raise HTTPException(
            status_code=404,
            detail=f"Resumable state {state_code} not configured for project {project_id}"
        )
    
    # Update only provided fields
    update_data = resumable_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_resumable, field, value)
    
    db_resumable.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_resumable)
    
    return db_resumable


# ============================================================================
# RESUME REQUESTS
# ============================================================================

@router.post(
    "/builds/{build_id}/resume",
    response_model=models.ResumeRequestResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["resume"]
)
def create_resume_request(
    build_id: str,
    resume_request: models.ResumeRequestCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_write),
):
    """
    Request to resume a build from a specific state. Requires write permission.
    
    This creates a resume request that can be picked up by the orchestrator
    or triggered manually through CI/CD.
    """
    # Validate build exists
    db_build = db.query(models.Build).filter(models.Build.id == build_id).first()
    if not db_build:
        raise HTTPException(status_code=404, detail=f"Build {build_id} not found")
    
    # Validate resume_from_state is valid
    if resume_request.resume_from_state < 0:
        raise HTTPException(status_code=400, detail="resume_from_state must be >= 0")
    
    if resume_request.resume_to_state is not None and resume_request.resume_to_state <= resume_request.resume_from_state:
        raise HTTPException(
            status_code=400,
            detail="resume_to_state must be greater than resume_from_state"
        )
    
    now = datetime.utcnow()
    db_resume = models.ResumeRequest(
        id=str(uuid.uuid4()),
        build_id=build_id,
        resume_from_state=resume_request.resume_from_state,
        resume_to_state=resume_request.resume_to_state,
        resume_reason=resume_request.resume_reason,
        requested_by=resume_request.requested_by or str(current_user.id),
        request_source=resume_request.request_source,
        orchestration_status='pending',
        metadata=resume_request.metadata,
        created_at=now,
        updated_at=now
    )
    
    db.add(db_resume)
    db.commit()
    db.refresh(db_resume)
    
    return db_resume


@router.get(
    "/builds/{build_id}/resume-requests",
    response_model=List[models.ResumeRequestResponse],
    tags=["resume"]
)
def list_resume_requests(
    build_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user_or_api_key),
):
    """
    List all resume requests for a build.
    """
    # Validate build exists
    db_build = db.query(models.Build).filter(models.Build.id == build_id).first()
    if not db_build:
        raise HTTPException(status_code=404, detail=f"Build {build_id} not found")
    
    requests = db.query(models.ResumeRequest).filter(
        models.ResumeRequest.build_id == build_id
    ).order_by(desc(models.ResumeRequest.created_at)).all()
    
    return requests


@router.get(
    "/resume-requests/{request_id}",
    response_model=models.ResumeRequestResponse,
    tags=["resume"]
)
def get_resume_request(
    request_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user_or_api_key),
):
    """
    Get details of a specific resume request.
    """
    resume_request = db.query(models.ResumeRequest).filter(
        models.ResumeRequest.id == request_id
    ).first()
    
    if not resume_request:
        raise HTTPException(status_code=404, detail=f"Resume request {request_id} not found")
    
    return resume_request


@router.patch(
    "/resume-requests/{request_id}",
    response_model=models.ResumeRequestResponse,
    tags=["resume"]
)
def update_resume_request(
    request_id: str,
    resume_update: models.ResumeRequestUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_write),
):
    """
    Update resume request status. Requires write permission.
    
    Typically used by orchestrator to update job status.
    """
    db_resume = db.query(models.ResumeRequest).filter(
        models.ResumeRequest.id == request_id
    ).first()
    
    if not db_resume:
        raise HTTPException(status_code=404, detail=f"Resume request {request_id} not found")
    
    # Update only provided fields
    update_data = resume_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_resume, field, value)
    
    db_resume.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_resume)
    
    return db_resume


# ============================================================================
# RESUME CONTEXT
# ============================================================================

@router.get(
    "/builds/{build_id}/resume-context",
    response_model=models.ResumeContext,
    tags=["resume"]
)
def get_resume_context(
    build_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user_or_api_key),
):
    """
    Get complete context needed to resume a build.
    
    Returns:
    - Build information
    - Current and last successful state
    - All resumable artifacts
    - All variables
    - Resumable state configuration (if available)
    
    This endpoint provides everything needed to restore a build to a previous
    state and continue execution.
    """
    # Validate build exists
    db_build = db.query(models.Build).filter(models.Build.id == build_id).first()
    if not db_build:
        raise HTTPException(status_code=404, detail=f"Build {build_id} not found")
    
    # Get current state from build
    current_state = db_build.current_state if hasattr(db_build, 'current_state') else 0
    
    # Get last successful state from build_states
    last_successful_state = db.query(models.BuildState).filter(
        models.BuildState.build_id == build_id,
        models.BuildState.status == 'completed'
    ).order_by(desc(models.BuildState.created_at)).first()
    
    last_state_code = last_successful_state.state if last_successful_state else 0
    
    # Get all resumable artifacts
    artifacts = db.query(models.BuildArtifact).filter(
        models.BuildArtifact.build_id == build_id,
        models.BuildArtifact.is_resumable == True,
        models.BuildArtifact.deleted_at.is_(None)
    ).order_by(models.BuildArtifact.state_code).all()
    
    # Get all variables as dictionary
    variables_list = db.query(models.BuildVariable).filter(
        models.BuildVariable.build_id == build_id
    ).all()
    
    variables_dict = {}
    for var in variables_list:
        if var.is_sensitive:
            variables_dict[var.variable_key] = "******"
        else:
            variables_dict[var.variable_key] = var.variable_value
    
    # Get resumable state config if available
    resumable_state_config = None
    if db_build.project_id:
        resumable_state_config = db.query(models.ResumableState).filter(
            models.ResumableState.project_id == db_build.project_id,
            models.ResumableState.state_code == current_state
        ).first()
    
    # Determine resume_from_state
    # If there's a failed state, resume from there; otherwise use current state
    failed_state = db.query(models.BuildState).filter(
        models.BuildState.build_id == build_id,
        models.BuildState.status.in_(['failed', 'error'])
    ).order_by(desc(models.BuildState.created_at)).first()
    
    failed_state_code = failed_state.state if failed_state else None
    resume_from_state = failed_state_code if failed_state_code else current_state
    
    context = models.ResumeContext(
        build_id=build_id,
        current_state=current_state,
        last_successful_state=last_state_code,
        failed_state=failed_state_code,
        resume_from_state=resume_from_state,
        artifacts=[models.BuildArtifactResponse.from_orm(a) for a in artifacts],
        variables=variables_dict,
        resumable_state_config=models.ResumableStateResponse.from_orm(resumable_state_config) if resumable_state_config else None
    )
    
    return context


# ============================================================================
# BUILD JOBS
# ============================================================================

@router.post(
    "/builds/{build_id}/jobs",
    response_model=models.BuildJobResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["resume"]
)
def create_build_job(
    build_id: str,
    job: models.BuildJobCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_write),
):
    """
    Link a CI/CD job to a build. Requires write permission.
    
    Tracks job execution information for builds and resumes.
    """
    # Validate build exists
    db_build = db.query(models.Build).filter(models.Build.id == build_id).first()
    if not db_build:
        raise HTTPException(status_code=404, detail=f"Build {build_id} not found")
    
    now = datetime.utcnow()
    db_job = models.BuildJob(
        id=str(uuid.uuid4()),
        build_id=build_id,
        platform=job.platform,
        pipeline_name=job.pipeline_name,
        job_name=job.job_name,
        job_url=job.job_url,
        job_id=job.job_id,
        build_number=job.build_number,
        triggered_by=job.triggered_by,
        trigger_source=job.trigger_source,
        status=job.status or 'pending',
        is_resume_job=job.is_resume_job,
        resumed_from_state=job.resumed_from_state,
        parent_job_id=job.parent_job_id,
        created_at=now,
        updated_at=now
    )
    
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    
    return db_job


@router.get(
    "/builds/{build_id}/jobs",
    response_model=List[models.BuildJobResponse],
    tags=["resume"]
)
def list_build_jobs(
    build_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user_or_api_key),
):
    """
    List all CI/CD jobs for a build.
    """
    # Validate build exists
    db_build = db.query(models.Build).filter(models.Build.id == build_id).first()
    if not db_build:
        raise HTTPException(status_code=404, detail=f"Build {build_id} not found")
    
    jobs = db.query(models.BuildJob).filter(
        models.BuildJob.build_id == build_id
    ).order_by(desc(models.BuildJob.created_at)).all()
    
    return jobs


@router.patch(
    "/builds/{build_id}/jobs/{job_id}",
    response_model=models.BuildJobResponse,
    tags=["resume"]
)
def update_build_job(
    build_id: str,
    job_id: str,
    job_update: models.BuildJobUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_write),
):
    """
    Update build job status. Requires write permission.
    """
    db_job = db.query(models.BuildJob).filter(
        models.BuildJob.id == job_id,
        models.BuildJob.build_id == build_id
    ).first()
    
    if not db_job:
        raise HTTPException(
            status_code=404,
            detail=f"Build job {job_id} not found for build {build_id}"
        )
    
    # Update only provided fields
    update_data = job_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_job, field, value)
    
    db_job.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_job)
    
    return db_job
