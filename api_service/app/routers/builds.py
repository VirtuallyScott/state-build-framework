"""
Build management endpoints for the Build State API.
"""
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List

from ..models import BuildCreate, BuildResponse, StateTransition, StateResponse, FailureRecord
from ..core.auth import get_current_user_or_api_key
from ..core.database import db
from ..dependencies import get_db

router = APIRouter()


@router.post("/builds", response_model=dict)
async def create_build(
    build: BuildCreate,
    current_user: dict = Depends(get_current_user_or_api_key),
    db_conn=Depends(get_db)
):
    """Create a new build."""
    build_id = str(uuid.uuid4())

    insert_query = """
    INSERT INTO builds (id, platform, image_type, description, current_state, status, created_at, updated_at, metadata)
    VALUES (%s, %s, %s, %s, 0, 'running', %s, %s, %s)
    """ if db_conn.db_type == "postgresql" else """
    INSERT INTO builds (id, platform, image_type, description, current_state, status, created_at, updated_at, metadata)
    VALUES (?, ?, ?, ?, 0, 'running', ?, ?, ?)
    """

    import json
    metadata_json = json.dumps(build.metadata) if build.metadata else None
    now = datetime.utcnow()

    db_conn.execute_query(
        insert_query,
        (build_id, build.platform, build.image_type, build.description, now, now, metadata_json),
        fetch=False
    )

    # Add initial state to history
    history_query = """
    INSERT INTO state_history (build_id, state, status, message, created_at)
    VALUES (%s, 0, 'running', 'Build initialized', %s)
    """ if db_conn.db_type == "postgresql" else """
    INSERT INTO state_history (build_id, state, status, message, created_at)
    VALUES (?, 0, 'running', 'Build initialized', ?)
    """

    db_conn.execute_query(history_query, (build_id, now), fetch=False)

    return {
        "id": build_id,
        "platform": build.platform,
        "image_type": build.image_type,
        "description": build.description,
        "current_state": 0,
        "status": "running"
    }


@router.post("/builds/{build_uuid}/state")
async def update_build_state(
    build_uuid: str,
    state_update: StateTransition,
    current_user: dict = Depends(get_current_user_or_api_key),
    db_conn=Depends(get_db)
):
    """Update build state."""
    # Validate state code
    if not (0 <= state_update.state_code <= 100):
        raise HTTPException(status_code=400, detail="State code must be between 0 and 100")

    # Check if build exists
    build_query = """
    SELECT id, current_state, status FROM builds WHERE id = %s
    """ if db_conn.db_type == "postgresql" else """
    SELECT id, current_state, status FROM builds WHERE id = ?
    """

    builds = db_conn.execute_query(build_query, (build_uuid,))
    if not builds:
        raise HTTPException(status_code=404, detail="Build not found")

    current_build = builds[0]

    # Determine new status based on state
    if state_update.state_code == 100:
        new_status = "completed"
    elif state_update.state_code < current_build["current_state"]:
        new_status = "failed"  # Regression indicates failure
    else:
        new_status = "running"

    # Update build
    update_query = """
    UPDATE builds SET current_state = %s, status = %s, updated_at = %s
    WHERE id = %s
    """ if db_conn.db_type == "postgresql" else """
    UPDATE builds SET current_state = ?, status = ?, updated_at = ?
    WHERE id = ?
    """

    now = datetime.utcnow()
    db_conn.execute_query(update_query, (state_update.state_code, new_status, now, build_uuid), fetch=False)

    # Add to state history
    import json
    metadata_json = json.dumps(state_update.metadata) if state_update.metadata else None

    history_query = """
    INSERT INTO state_history (build_id, state, status, message, metadata, created_at)
    VALUES (%s, %s, %s, %s, %s, %s)
    """ if db_conn.db_type == "postgresql" else """
    INSERT INTO state_history (build_id, state, status, message, metadata, created_at)
    VALUES (?, ?, ?, ?, ?, ?)
    """

    db_conn.execute_query(
        history_query,
        (build_uuid, state_update.state_code, new_status, state_update.message, metadata_json, now),
        fetch=False
    )

    return {
        "build_id": build_uuid,
        "current_state": state_update.state_code,
        "status": new_status,
        "updated_at": now
    }


@router.post("/builds/{build_uuid}/failure")
async def record_build_failure(
    build_uuid: str,
    failure: FailureRecord,
    current_user: dict = Depends(get_current_user_or_api_key),
    db_conn=Depends(get_db)
):
    """Record a build failure."""
    # Update build status to failed
    update_query = """
    UPDATE builds SET status = 'failed', updated_at = %s
    WHERE id = %s
    """ if db_conn.db_type == "postgresql" else """
    UPDATE builds SET status = 'failed', updated_at = ?
    WHERE id = ?
    """

    now = datetime.utcnow()
    db_conn.execute_query(update_query, (now, build_uuid), fetch=False)

    # Add failure to state history
    import json
    metadata_json = json.dumps(failure.metadata) if failure.metadata else None

    history_query = """
    INSERT INTO state_history (build_id, state, status, message, error_message, error_code, metadata, created_at)
    VALUES (%s, (SELECT current_state FROM builds WHERE id = %s), 'failed', 'Build failure recorded', %s, %s, %s, %s)
    """ if db_conn.db_type == "postgresql" else """
    INSERT INTO state_history (build_id, state, status, message, error_message, error_code, metadata, created_at)
    VALUES (?, (SELECT current_state FROM builds WHERE id = ?), 'failed', 'Build failure recorded', ?, ?, ?, ?)
    """

    db_conn.execute_query(
        history_query,
        (build_uuid, build_uuid, failure.error_message, failure.error_code, metadata_json, now),
        fetch=False
    )

    return {"message": "Build failure recorded", "build_id": build_uuid}


@router.get("/builds/{build_uuid}", response_model=BuildResponse)
async def get_build(
    build_uuid: str,
    current_user: dict = Depends(get_current_user_or_api_key),
    db_conn=Depends(get_db)
):
    """Get build details."""
    query = """
    SELECT id, platform, image_type, description, current_state, status, created_at, updated_at, metadata
    FROM builds
    WHERE id = %s
    """ if db_conn.db_type == "postgresql" else """
    SELECT id, platform, image_type, description, current_state, status, created_at, updated_at, metadata
    FROM builds
    WHERE id = ?
    """

    builds = db_conn.execute_query(query, (build_uuid,))
    if not builds:
        raise HTTPException(status_code=404, detail="Build not found")

    build = builds[0]

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
    build_query = """
    SELECT current_state, status, updated_at FROM builds WHERE id = %s
    """ if db_conn.db_type == "postgresql" else """
    SELECT current_state, status, updated_at FROM builds WHERE id = ?
    """

    builds = db_conn.execute_query(build_query, (build_uuid,))
    if not builds:
        raise HTTPException(status_code=404, detail="Build not found")

    build = builds[0]

    # Get state history
    history_query = """
    SELECT state, status, message, error_message, error_code, metadata, created_at
    FROM state_history
    WHERE build_id = %s
    ORDER BY created_at DESC
    LIMIT 10
    """ if db_conn.db_type == "postgresql" else """
    SELECT state, status, message, error_message, error_code, metadata, created_at
    FROM state_history
    WHERE build_id = ?
    ORDER BY created_at DESC
    LIMIT 10
    """

    history = db_conn.execute_query(history_query, (build_uuid,))

    # Parse metadata JSON in history
    import json
    for entry in history:
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
        state_history=history
    )