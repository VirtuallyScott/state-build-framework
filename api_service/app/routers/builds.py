"""
Build management endpoints for the Build State API.
"""
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from sqlalchemy.orm import Session, joinedload

from .. import models
from ..models import FailureRecord, BuildResponse, StateResponse, BuildStateResponse
from ..core.auth import get_current_user_or_api_key, require_write
from ..dependencies import get_db

router = APIRouter()


@router.post("/builds", response_model=BuildResponse, status_code=status.HTTP_201_CREATED)
def create_build(
    build: models.BuildCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_write),
):
    """
    Create a new build. Requires write permission.

    A new build is created and automatically placed in the project's defined
    initial state.
    """
    # Validate project exists and is active
    project = db.query(models.Project).filter(
        models.Project.id == build.project_id,
        models.Project.end_date == None
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Active project with id {build.project_id} not found")

    # Get initial state for the project
    initial_state = db.query(models.StateCode).filter(
        models.StateCode.project_id == build.project_id,
        models.StateCode.is_initial == True,
        models.StateCode.end_date == None
    ).first()

    if not initial_state:
        raise HTTPException(
            status_code=400,
            detail="No initial state defined for this project. Please create an initial state code."
        )

    now = datetime.utcnow()
    db_build = models.Build(
        id=uuid.uuid4(),
        project_id=build.project_id,
        platform_id=build.platform_id,
        os_version_id=build.os_version_id,
        image_type_id=build.image_type_id,
        os_distribution_id=build.os_distribution_id,
        cloud_provider_id=build.cloud_provider_id,
        image_variant_id=build.image_variant_id,
        description=build.description,
        current_state_code_id=initial_state.id,
        status="running",
        start_date=now,
        metadata=build.metadata
    )
    db.add(db_build)

    # Add initial state to build_states table
    initial_build_state = models.BuildState(
        id=uuid.uuid4(),
        build_id=db_build.id,
        state_code_id=initial_state.id,
        status="running",
        message="Build initialized",
        start_date=now
    )
    db.add(initial_build_state)

    db.commit()
    db.refresh(db_build)
    return db_build


@router.post("/builds/{build_id}/state", response_model=BuildStateResponse)
def update_build_state(
    build_id: uuid.UUID,
    state_update: models.StateTransition,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_write),
):
    """
    Transition a build to a new state. Requires write permission.
    """
    db_build = db.query(models.Build).filter(models.Build.id == build_id).first()
    if not db_build:
        raise HTTPException(status_code=404, detail="Build not found")

    if db_build.end_date is not None:
        raise HTTPException(status_code=400, detail="Cannot transition a completed or failed build.")

    # Get target state code
    target_state = db.query(models.StateCode).filter(
        models.StateCode.project_id == db_build.project_id,
        models.StateCode.name == state_update.state_name,
        models.StateCode.end_date == None
    ).first()

    if not target_state:
        raise HTTPException(
            status_code=400,
            detail=f"State '{state_update.state_name}' not found or is inactive for this project."
        )

    now = datetime.utcnow()

    # Determine new status
    if target_state.is_final:
        new_status = "completed"
        db_build.end_date = now
    elif target_state.is_error:
        new_status = "failed"
        db_build.end_date = now
    else:
        new_status = "running"

    # Update build
    db_build.current_state_code_id = target_state.id
    db_build.status = new_status

    # Create new build state entry
    new_build_state = models.BuildState(
        id=uuid.uuid4(),
        build_id=build_id,
        state_code_id=target_state.id,
        status=new_status,
        message=state_update.message,
        metadata=state_update.metadata,
        start_date=now
    )
    db.add(new_build_state)
    db.commit()
    db.refresh(new_build_state)

    return new_build_state


@router.post("/builds/{build_id}/failure", response_model=BuildStateResponse)
def record_build_failure(
    build_id: uuid.UUID,
    failure: FailureRecord,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_write),
):
    """
    Record a build failure outside of a normal state transition. Requires write permission.
    This forces the build into a 'failed' state.
    """
    db_build = db.query(models.Build).filter(models.Build.id == build_id).first()
    if not db_build:
        raise HTTPException(status_code=404, detail="Build not found")

    if db_build.end_date is not None:
        raise HTTPException(status_code=400, detail="Build has already been completed or failed.")

    now = datetime.utcnow()

    # Update build status to failed
    db_build.status = 'failed'
    db_build.end_date = now

    # Create a failure record in the build_states table
    failure_state = models.BuildState(
        id=uuid.uuid4(),
        build_id=build_id,
        state_code_id=db_build.current_state_code_id, # Record failure at the state it happened
        status='failed',
        message='Build failure recorded',
        error_message=failure.error_message,
        error_code=failure.error_code,
        metadata=failure.metadata,
        start_date=now
    )
    db.add(failure_state)
    db.commit()
    db.refresh(failure_state)

    return failure_state


@router.get("/builds", response_model=List[BuildResponse])
def list_builds(
    skip: int = 0,
    limit: int = 100,
    project_id: uuid.UUID = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_api_key),
):
    """
    List builds, with optional filtering by project.
    """
    query = db.query(models.Build).options(
        joinedload(models.Build.project),
        joinedload(models.Build.current_state_code)
    )

    if project_id:
        query = query.filter(models.Build.project_id == project_id)

    builds = query.order_by(models.Build.start_date.desc()).offset(skip).limit(limit).all()
    return builds


@router.get("/builds/{build_id}", response_model=BuildResponse)
def get_build(
    build_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_api_key),
):
    """
    Get detailed information for a specific build.
    """
    db_build = db.query(models.Build).options(
        joinedload(models.Build.project),
        joinedload(models.Build.platform),
        joinedload(models.Build.os_version),
        joinedload(models.Build.image_type),
        joinedload(models.Build.os_distribution),
        joinedload(models.Build.cloud_provider),
        joinedload(models.Build.image_variant),
        joinedload(models.Build.current_state_code),
        joinedload(models.Build.states).subqueryload(models.BuildState.state_code)
    ).filter(models.Build.id == build_id).first()

    if not db_build:
        raise HTTPException(status_code=404, detail="Build not found")

    return db_build



@router.get("/builds/{build_id}/state", response_model=StateResponse)
def get_build_state_history(
    build_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_api_key),
):
    """
    Get the current state and historical state transitions for a build.
    """
    db_build = db.query(models.Build).options(
        joinedload(models.Build.current_state_code)
    ).filter(models.Build.id == build_id).first()

    if not db_build:
        raise HTTPException(status_code=404, detail="Build not found")

    history = db.query(models.BuildState).options(
        joinedload(models.BuildState.state_code)
    ).filter(models.BuildState.build_id == build_id).order_by(
        models.BuildState.start_date.desc()
    ).all()

    return models.StateResponse(
        build_id=db_build.id,
        current_state=db_build.current_state_code.name,
        status=db_build.status,
        last_transition=db_build.updated_at,
        state_history=history
    )











@router.get("/builds/{build_uuid}", response_model=BuildResponse)
async def get_build(
    build_uuid: str,
    current_user: dict = Depends(get_current_user_or_api_key),
    db_conn=Depends(get_db)
):
    """Get build details."""
    query = db_conn.execute_query("""
        SELECT b.id, b.project_id, b.platform, b.image_type, b.description,
               sc.name as current_state, b.status, b.created_at, b.updated_at, b.metadata,
               p.name as project_name
        FROM builds b
        JOIN state_codes sc ON b.current_state_code_id = sc.id
        JOIN projects p ON b.project_id = p.id
        WHERE b.id = ?
    """, (build_uuid,))

    if not query:
        raise HTTPException(status_code=404, detail="Build not found")

    build = query[0]

    # Parse metadata JSON
    import json
    if build["metadata"]:
        try:
            build["metadata"] = json.loads(build["metadata"])
        except:
            build["metadata"] = None

    return BuildResponse(**build)


@router.get("/builds/{build_uuid}/state", response_model=StateResponse)
async def get_build_state(
    build_uuid: str,
    current_user: dict = Depends(get_current_user_or_api_key),
    db_conn=Depends(get_db)
):
    """Get build state information."""
    # Get current build state
    build_query = db_conn.execute_query("""
        SELECT b.current_state_code_id, b.status, b.updated_at, sc.name as current_state
        FROM builds b
        JOIN state_codes sc ON b.current_state_code_id = sc.id
        WHERE b.id = ?
    """, (build_uuid,))

    if not build_query:
        raise HTTPException(status_code=404, detail="Build not found")

    build = build_query[0]

    # Get state history
    history_query = db_conn.execute_query("""
        SELECT sc.name as state, bs.status, bs.message, bs.error_message,
               bs.error_code, bs.metadata, bs.created_at
        FROM build_states bs
        JOIN state_codes sc ON bs.state_code_id = sc.id
        WHERE bs.build_id = ?
        ORDER BY bs.created_at DESC
        LIMIT 10
    """, (build_uuid,))

    # Parse metadata JSON in history
    import json
    for entry in history_query:
        if entry["metadata"]:
            try:
                entry["metadata"] = json.loads(entry["metadata"])
            except:
                entry["metadata"] = None

    return StateResponse(
        build_id=build_uuid,
        current_state=build["current_state"],
        status=build["status"],
        last_transition=build["updated_at"],
        state_history=history_query
    )


@router.get("/builds", response_model=List[BuildResponse])
async def list_builds(
    skip: int = 0,
    limit: int = 100,
    project_id: str = None,
    current_user: dict = Depends(get_current_user_or_api_key),
    db_conn=Depends(get_db)
):
    """List builds with optional project filter."""
    where_clause = ""
    params = []

    if project_id:
        where_clause = "WHERE b.project_id = ?"
        params.append(project_id)

    query = f"""
        SELECT b.id, b.project_id, b.platform, b.image_type, b.description,
               sc.name as current_state, b.status, b.created_at, b.updated_at, b.metadata,
               p.name as project_name
        FROM builds b
        JOIN state_codes sc ON b.current_state_code_id = sc.id
        JOIN projects p ON b.project_id = p.id
        {where_clause}
        ORDER BY b.created_at DESC
        LIMIT ? OFFSET ?
    """
    params.extend([limit, skip])

    builds = db_conn.execute_query(query, tuple(params))

    # Parse metadata JSON
    import json
    for build in builds:
        if build["metadata"]:
            try:
                build["metadata"] = json.loads(build["metadata"])
            except:
                build["metadata"] = None

    return [BuildResponse(**build) for build in builds]