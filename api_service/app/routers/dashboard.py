"""
Dashboard and reporting endpoints for the Build State API.
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func

from .. import models
from ..dependencies import get_db
from ..core.auth import get_current_user_or_api_key

router = APIRouter()


@router.get("/dashboard/summary", response_model=models.DashboardSummary)
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_api_key)
):
    """
    Get dashboard summary statistics.
    """
    total_builds = db.query(models.Build).count()
    active_builds = db.query(models.Build).filter(models.Build.status == 'running').count()
    completed_builds = db.query(models.Build).filter(models.Build.status == 'completed').count()
    failed_builds = db.query(models.Build).filter(models.Build.status == 'failed').count()

    platform_results = db.query(
        models.Platform.name,
        func.count(models.Build.id)
    ).join(models.Build, models.Build.platform_id == models.Platform.id).group_by(models.Platform.name).all()
    builds_by_platform = {name: count for name, count in platform_results}

    state_results = db.query(
        models.StateCode.name,
        func.count(models.Build.id)
    ).join(models.Build, models.Build.current_state_code_id == models.StateCode.id).group_by(models.StateCode.name).all()
    builds_by_state = {name: count for name, count in state_results}

    return models.DashboardSummary(
        total_builds=total_builds,
        active_builds=active_builds,
        completed_builds=completed_builds,
        failed_builds=failed_builds,
        builds_by_platform=builds_by_platform,
        builds_by_state=builds_by_state
    )


@router.get("/dashboard/recent", response_model=List[models.BuildResponse])
def get_recent_builds(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_api_key)
):
    """
    Get recently updated builds.
    """
    recent_builds = db.query(models.Build).order_by(
        models.Build.updated_at.desc()
    ).limit(limit).all()
    return recent_builds


@router.get("/dashboard/platform/{platform_id}", response_model=Dict)
def get_platform_dashboard(
    platform_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_api_key)
):
    """
    Get dashboard data for a specific platform.
    """
    platform = db.query(models.Platform).filter(models.Platform.id == platform_id).first()
    if not platform:
        raise HTTPException(status_code=404, detail="Platform not found")

    stats_query = db.query(
        func.count(models.Build.id).label("total_builds"),
        func.min(models.Build.updated_at).label("oldest_build"),
        func.max(models.Build.updated_at).label("newest_build")
    ).filter(models.Build.platform_id == platform_id)
    stats = stats_query.one()

    recent_builds = db.query(models.Build).filter(
        models.Build.platform_id == platform_id
    ).order_by(models.Build.updated_at.desc()).limit(5).all()

    state_dist_query = db.query(
        models.StateCode.name.label("state_name"),
        func.count(models.Build.id).label("count")
    ).join(models.Build, models.Build.current_state_code_id == models.StateCode.id).filter(
        models.Build.platform_id == platform_id
    ).group_by(models.StateCode.name).order_by(models.StateCode.name)
    state_dist = state_dist_query.all()
    state_distribution = {row.state_name: row.count for row in state_dist}

    return {
        "platform": platform.name,
        "statistics": {
            "total_builds": stats.total_builds,
            "oldest_build": stats.oldest_build,
            "newest_build": stats.newest_build,
        },
        "recent_builds": recent_builds,
        "state_distribution": state_distribution
    }

