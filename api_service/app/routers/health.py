"""
Health check endpoints for the Build State API.
"""
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
import redis

from .. import models
from ..dependencies import get_db
from ..core.config import settings

router = APIRouter()


@router.get("/", response_model=dict, include_in_schema=False)
async def root():
    """Root endpoint."""
    return {"message": "Build State API", "version": "1.0.0"}


@router.get("/health", response_model=models.HealthResponse, tags=["Health"])
async def health_check():
    """Basic health check endpoint."""
    return models.HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow()
    )


@router.get("/ready", response_model=models.ReadinessResponse, tags=["Health"])
def readiness_check(db: Session = Depends(get_db)):
    """
    Readiness check to verify database and cache connections.
    """
    # Check database connection
    try:
        db.execute(text("SELECT 1"))
        db_status = "ready"
    except Exception:
        db_status = "unready"

    # Check cache connection
    cache_status = "disabled"
    if settings.redis_url:
        try:
            redis_client = redis.from_url(settings.redis_url)
            redis_client.ping()
            cache_status = "ready"
        except Exception:
            cache_status = "unready"

    is_ready = db_status == "ready" and cache_status in ("ready", "disabled")

    return models.ReadinessResponse(
        status="ready" if is_ready else "unready",
        database=db_status,
        cache=cache_status,
        timestamp=datetime.utcnow()
    )


@router.get("/status", response_model=models.StatusResponse, tags=["Health"])
def status_check(db: Session = Depends(get_db)):
    """
    Detailed status check endpoint providing component information.
    """
    # Database info
    db_info = {"type": db.bind.dialect.name, "status": "unknown"}
    try:
        builds_count = db.query(models.Build).count()
        db_info["status"] = "connected"
        db_info["builds_count"] = builds_count
    except Exception as e:
        db_info["status"] = f"error: {str(e)}"

    # Cache info
    cache_info = {"status": "disabled"}
    if settings.redis_url:
        try:
            redis_client = redis.from_url(settings.redis_url)
            redis_client.ping()
            cache_info["status"] = "connected"
        except Exception as e:
            cache_info["status"] = f"error: {str(e)}"

    return models.StatusResponse(
        status="operational",
        uptime="unknown",  # Would need to track start time
        version="1.0.0",
        database=db_info,
        cache=cache_info,
        timestamp=datetime.utcnow()
    )
