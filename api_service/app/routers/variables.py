"""
Build Variable management endpoints for the Build State API.
Stores build-specific variables needed for resumption (VM IDs, network config, etc.)
"""
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional, Dict
from sqlalchemy.orm import Session

from .. import models
from ..core.auth import get_current_user_or_api_key, require_write
from ..dependencies import get_db

router = APIRouter()


@router.post(
    "/builds/{build_id}/variables",
    response_model=models.BuildVariableResponse,
    status_code=status.HTTP_201_CREATED
)
def set_variable(
    build_id: str,
    variable: models.BuildVariableCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_write),
):
    """
    Set a build variable. Requires write permission.
    
    If the variable already exists, it will be updated.
    Variables store context needed to resume builds (VM IDs, network config, etc.)
    """
    # Validate build exists
    db_build = db.query(models.Build).filter(models.Build.id == build_id).first()
    if not db_build:
        raise HTTPException(status_code=404, detail=f"Build {build_id} not found")
    
    # Check if variable already exists
    db_variable = db.query(models.BuildVariable).filter(
        models.BuildVariable.build_id == build_id,
        models.BuildVariable.variable_key == variable.variable_key
    ).first()
    
    now = datetime.utcnow()
    
    if db_variable:
        # Update existing variable
        db_variable.variable_value = variable.variable_value
        db_variable.variable_type = variable.variable_type
        db_variable.set_at_state = variable.set_at_state
        db_variable.is_sensitive = variable.is_sensitive
        db_variable.is_required_for_resume = variable.is_required_for_resume
        db_variable.updated_at = now
    else:
        # Create new variable
        db_variable = models.BuildVariable(
            id=str(uuid.uuid4()),
            build_id=build_id,
            variable_key=variable.variable_key,
            variable_value=variable.variable_value,
            variable_type=variable.variable_type,
            set_at_state=variable.set_at_state,
            is_sensitive=variable.is_sensitive,
            is_required_for_resume=variable.is_required_for_resume,
            created_at=now,
            updated_at=now
        )
        db.add(db_variable)
    
    db.commit()
    db.refresh(db_variable)
    
    return db_variable


@router.get(
    "/builds/{build_id}/variables",
    response_model=List[models.BuildVariableResponse]
)
def list_variables(
    build_id: str,
    required_for_resume: Optional[bool] = Query(None, description="Filter by required for resume flag"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user_or_api_key),
):
    """
    List all variables for a build with optional filters.
    """
    # Validate build exists
    db_build = db.query(models.Build).filter(models.Build.id == build_id).first()
    if not db_build:
        raise HTTPException(status_code=404, detail=f"Build {build_id} not found")
    
    query = db.query(models.BuildVariable).filter(
        models.BuildVariable.build_id == build_id
    )
    
    if required_for_resume is not None:
        query = query.filter(models.BuildVariable.is_required_for_resume == required_for_resume)
    
    variables = query.order_by(models.BuildVariable.variable_key).all()
    
    return variables


@router.get(
    "/builds/{build_id}/variables/dict",
    response_model=Dict[str, str]
)
def get_variables_dict(
    build_id: str,
    required_for_resume: Optional[bool] = Query(None, description="Filter by required for resume flag"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user_or_api_key),
):
    """
    Get all variables for a build as a simple key-value dictionary.
    
    Sensitive variables are masked with ******.
    Useful for scripts and automation.
    """
    # Validate build exists
    db_build = db.query(models.Build).filter(models.Build.id == build_id).first()
    if not db_build:
        raise HTTPException(status_code=404, detail=f"Build {build_id} not found")
    
    query = db.query(models.BuildVariable).filter(
        models.BuildVariable.build_id == build_id
    )
    
    if required_for_resume is not None:
        query = query.filter(models.BuildVariable.is_required_for_resume == required_for_resume)
    
    variables = query.all()
    
    # Build dictionary, masking sensitive values
    result = {}
    for var in variables:
        if var.is_sensitive:
            result[var.variable_key] = "******"
        else:
            result[var.variable_key] = var.variable_value
    
    return result


@router.get(
    "/builds/{build_id}/variables/{variable_key}",
    response_model=models.BuildVariableResponse
)
def get_variable(
    build_id: str,
    variable_key: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user_or_api_key),
):
    """
    Get a specific variable by key.
    """
    variable = db.query(models.BuildVariable).filter(
        models.BuildVariable.build_id == build_id,
        models.BuildVariable.variable_key == variable_key
    ).first()
    
    if not variable:
        raise HTTPException(
            status_code=404,
            detail=f"Variable '{variable_key}' not found for build {build_id}"
        )
    
    return variable


@router.patch(
    "/builds/{build_id}/variables/{variable_key}",
    response_model=models.BuildVariableResponse
)
def update_variable(
    build_id: str,
    variable_key: str,
    variable_update: models.BuildVariableUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_write),
):
    """
    Update a variable. Requires write permission.
    """
    db_variable = db.query(models.BuildVariable).filter(
        models.BuildVariable.build_id == build_id,
        models.BuildVariable.variable_key == variable_key
    ).first()
    
    if not db_variable:
        raise HTTPException(
            status_code=404,
            detail=f"Variable '{variable_key}' not found for build {build_id}"
        )
    
    # Update only provided fields
    update_data = variable_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_variable, field, value)
    
    db_variable.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_variable)
    
    return db_variable


@router.delete(
    "/builds/{build_id}/variables/{variable_key}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_variable(
    build_id: str,
    variable_key: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_write),
):
    """
    Delete a variable. Requires write permission.
    """
    db_variable = db.query(models.BuildVariable).filter(
        models.BuildVariable.build_id == build_id,
        models.BuildVariable.variable_key == variable_key
    ).first()
    
    if not db_variable:
        raise HTTPException(
            status_code=404,
            detail=f"Variable '{variable_key}' not found for build {build_id}"
        )
    
    db.delete(db_variable)
    db.commit()
    
    return None
