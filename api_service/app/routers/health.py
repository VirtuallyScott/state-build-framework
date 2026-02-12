"""
Health check endpoints for the Build State API.
"""
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy import text

from ..models import HealthResponse, ReadinessResponse, StatusResponse
from ..core.database import db
from ..dependencies import get_db

router = APIRouter()


@router.get("/", response_model=dict)
async def root():
    """Root endpoint."""
    return {"message": "Build State API", "version": "1.0.0"}


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Basic health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow()
    )


@router.get("/ready", response_model=ReadinessResponse)
async def readiness_check(db_conn=Depends(get_db)):
    """Readiness check endpoint."""
    # Check database connection
    try:
        db_conn.execute_query("SELECT 1", fetch=False)
        db_status = "ready"
    except Exception:
        db_status = "unready"

    # Check cache connection
    try:
        if db_conn.redis_client:
            db_conn.redis_client.ping()
            cache_status = "ready"
        else:
            cache_status = "disabled"
    except Exception:
        cache_status = "unready"

    return ReadinessResponse(
        status="ready" if db_status == "ready" else "unready",
        database=db_status,
        cache=cache_status,
        timestamp=datetime.utcnow()
    )


@router.get("/status", response_model=StatusResponse)
async def status_check(db_conn=Depends(get_db)):
    """Detailed status check endpoint."""
    # Database info
    db_info = {"type": db_conn.db_type, "status": "unknown"}
    try:
        result = db_conn.execute_query("SELECT COUNT(*) as count FROM builds")
        db_info["status"] = "connected"
        db_info["builds_count"] = result[0]["count"] if result else 0
    except Exception as e:
        db_info["status"] = f"error: {str(e)}"

    # Cache info
    cache_info = {"status": "disabled"}
    if db_conn.redis_client:
        try:
            db_conn.redis_client.ping()
            cache_info["status"] = "connected"
        except Exception as e:
            cache_info["status"] = f"error: {str(e)}"

    return StatusResponse(
        status="operational",
        uptime="unknown",  # Would need to track start time
        version="1.0.0",
        database=db_info,
        cache=cache_info,
        timestamp=datetime.utcnow()
    )