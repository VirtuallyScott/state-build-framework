"""
State Codes API router.
"""
import uuid
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models
from ..dependencies import get_db
from ..core.auth import get_current_user_or_api_key, require_write, require_admin

router = APIRouter()


@router.post("/projects/{project_id}/state-codes", response_model=models.StateCodeResponse, status_code=status.HTTP_201_CREATED)
def create_state_code(
    project_id: uuid.UUID,
    state_code: models.StateCodeCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_write)
):
    """
    Create a new state code for a project. Requires write permission.
    """
    # Check if project exists and is active
    project = db.query(models.Project).filter(
        models.Project.id == project_id,
        models.Project.end_date == None
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Active project with id {project_id} not found")

    # Check if state code name already exists for this project
    existing_state_code = db.query(models.StateCode).filter(
        models.StateCode.project_id == project_id,
        models.StateCode.name == state_code.name,
        models.StateCode.end_date == None
    ).first()
    if existing_state_code:
        raise HTTPException(
            status_code=400,
            detail=f"An active state code with name '{state_code.name}' already exists for this project."
        )

    # If creating an initial state, ensure no other initial state is active
    if state_code.is_initial:
        active_initial_state = db.query(models.StateCode).filter(
            models.StateCode.project_id == project_id,
            models.StateCode.is_initial == True,
            models.StateCode.end_date == None
        ).first()
        if active_initial_state:
            raise HTTPException(
                status_code=400,
                detail="An active initial state already exists for this project. Deactivate it before creating a new one."
            )

    db_state_code = models.StateCode(
        id=uuid.uuid4(),
        project_id=project_id,
        **state_code.dict(),
        start_date=datetime.utcnow()
    )
    db.add(db_state_code)
    db.commit()
    db.refresh(db_state_code)
    return db_state_code


@router.get("/projects/{project_id}/state-codes", response_model=List[models.StateCodeResponse])
def list_state_codes(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user_or_api_key)
):
    """
    List all active state codes for a project. Requires authentication.
    """
    # Check if project exists
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    state_codes = db.query(models.StateCode).filter(
        models.StateCode.project_id == project_id,
        models.StateCode.end_date == None
    ).order_by(models.StateCode.name).all()

    return state_codes


@router.get("/projects/{project_id}/state-codes/{state_code_id}", response_model=models.StateCodeResponse)
def get_state_code(
    project_id: uuid.UUID,
    state_code_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_api_key)
):
    """
    Get a specific active state code.
    """
    state_code = db.query(models.StateCode).filter(
        models.StateCode.id == state_code_id,
        models.StateCode.project_id == project_id,
        models.StateCode.end_date == None
    ).first()

    if not state_code:
        raise HTTPException(status_code=404, detail="Active state code not found")

    return state_code


@router.put("/projects/{project_id}/state-codes/{state_code_id}", response_model=models.StateCodeResponse)
def update_state_code(
    project_id: uuid.UUID,
    state_code_id: uuid.UUID,
    state_code_update: models.StateCodeUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_write)
):
    """
    Update a state code. Requires write permission.
    """
    db_state_code = db.query(models.StateCode).filter(
        models.StateCode.id == state_code_id,
        models.StateCode.project_id == project_id,
        models.StateCode.end_date == None
    ).first()

    if not db_state_code:
        raise HTTPException(status_code=404, detail="Active state code not found")

    update_data = state_code_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_state_code, key, value)

    db.commit()
    db.refresh(db_state_code)
    return db_state_code


@router.delete("/projects/{project_id}/state-codes/{state_code_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_state_code(
    project_id: uuid.UUID,
    state_code_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    """
    Deactivate a state code (soft delete). Requires admin permission.
    """
    db_state_code = db.query(models.StateCode).filter(
        models.StateCode.id == state_code_id,
        models.StateCode.project_id == project_id,
        models.StateCode.end_date == None
    ).first()

    if not db_state_code:
        raise HTTPException(status_code=404, detail="Active state code not found")

    # Check if state code is used by any active builds
    active_builds_count = db.query(models.Build).filter(
        models.Build.current_state_code_id == state_code_id,
        models.Build.end_date == None
    ).count()

    if active_builds_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot deactivate state code. It is currently used by {active_builds_count} active builds."
        )

    db_state_code.end_date = datetime.utcnow()
    db.commit()

    return None