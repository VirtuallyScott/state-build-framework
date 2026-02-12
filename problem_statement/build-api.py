# State-Based Build Framework API Service
# FastAPI service providing REST API for build state management

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import sqlite3
import uuid
import os
from contextlib import contextmanager

app = FastAPI(
    title="State-Based Build Framework API",
    description="REST API for managing multi-cloud IaaS image build states",
    version="1.0.0"
)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "builds.db")

# =============================================================================
# MODELS
# =============================================================================

class Platform(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    display_name: str
    cloud_provider: str
    region: Optional[str] = None

class OSVersion(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    display_name: str
    os_family: str
    major_version: int
    minor_version: Optional[int] = None

class ImageType(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    display_name: str
    description: Optional[str] = None

class BuildCreate(BaseModel):
    platform_name: str
    os_version_name: str
    image_type_name: str
    created_by: str
    concourse_pipeline_url: Optional[str] = None
    concourse_job_name: Optional[str] = None

class BuildUpdate(BaseModel):
    status: Optional[str] = None
    ami_id: Optional[str] = None
    image_id: Optional[str] = None
    packer_manifest: Optional[str] = None

class StateTransition(BaseModel):
    state: int
    status: str  # 'started', 'completed', 'failed'
    error_message: Optional[str] = None

class BuildFailure(BaseModel):
    state: int
    failure_type: str
    error_message: str
    component: str
    error_details: Optional[Dict[str, Any]] = None

# =============================================================================
# DATABASE HELPERS
# =============================================================================

@contextmanager
def get_db():
    conn = sqlite3.connect(DATABASE_URL)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """Initialize database with schema if it doesn't exist"""
    if not os.path.exists(DATABASE_URL):
        with get_db() as conn:
            with open('database-schema.sql', 'r') as f:
                conn.executescript(f.read())
            with open('sample-data.sql', 'r') as f:
                conn.executescript(f.read())

# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.on_event("startup")
async def startup_event():
    init_db()

@app.get("/")
async def root():
    return {"message": "State-Based Build Framework API", "version": "1.0.0"}

# -----------------------------------------------------------------------------
# BUILD ENDPOINTS
# -----------------------------------------------------------------------------

@app.post("/builds/", response_model=dict)
async def create_build(build: BuildCreate):
    """Create a new build"""
    with get_db() as conn:
        # Get IDs for the referenced entities
        platform = conn.execute(
            "SELECT id FROM platforms WHERE name = ?", (build.platform_name,)
        ).fetchone()
        if not platform:
            raise HTTPException(status_code=404, detail=f"Platform '{build.platform_name}' not found")

        os_version = conn.execute(
            "SELECT id FROM os_versions WHERE name = ?", (build.os_version_name,)
        ).fetchone()
        if not os_version:
            raise HTTPException(status_code=404, detail=f"OS version '{build.os_version_name}' not found")

        image_type = conn.execute(
            "SELECT id FROM image_types WHERE name = ?", (build.image_type_name,)
        ).fetchone()
        if not image_type:
            raise HTTPException(status_code=404, detail=f"Image type '{build.image_type_name}' not found")

        # Generate build number
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        build_number = f"{build.os_version_name}-{build.image_type_name}-{build.platform_name}-{timestamp}"

        build_id = str(uuid.uuid4())

        conn.execute("""
            INSERT INTO builds (
                id, build_number, platform_id, os_version_id, image_type_id,
                status, created_by, concourse_pipeline_url, concourse_job_name
            ) VALUES (?, ?, ?, ?, ?, 'pending', ?, ?, ?)
        """, (
            build_id, build_number, platform['id'], os_version['id'], image_type['id'],
            build.created_by, build.concourse_pipeline_url, build.concourse_job_name
        ))

        # Create initial state transition
        conn.execute("""
            INSERT INTO build_states (id, build_id, state, status, start_time)
            VALUES (?, ?, 0, 'started', ?)
        """, (str(uuid.uuid4()), build_id, datetime.now().isoformat()))

        conn.commit()

        return {"build_id": build_id, "build_number": build_number}

@app.get("/builds/{build_id}")
async def get_build(build_id: str):
    """Get build details"""
    with get_db() as conn:
        build = conn.execute("""
            SELECT
                b.*,
                p.display_name as platform_name,
                os.display_name as os_version_name,
                it.display_name as image_type_name
            FROM builds b
            JOIN platforms p ON b.platform_id = p.id
            JOIN os_versions os ON b.os_version_id = os.id
            JOIN image_types it ON b.image_type_id = it.id
            WHERE b.id = ?
        """, (build_id,)).fetchone()

        if not build:
            raise HTTPException(status_code=404, detail="Build not found")

        return dict(build)

@app.get("/builds/")
async def list_builds(
    status: Optional[str] = None,
    platform: Optional[str] = None,
    limit: int = Query(50, le=100),
    offset: int = 0
):
    """List builds with optional filtering"""
    with get_db() as conn:
        query = """
            SELECT
                b.id, b.build_number, b.current_state, b.status, b.start_time,
                b.end_time, b.created_by, b.concourse_pipeline_url,
                p.display_name as platform_name,
                os.display_name as os_version_name,
                it.display_name as image_type_name
            FROM builds b
            JOIN platforms p ON b.platform_id = p.id
            JOIN os_versions os ON b.os_version_id = os.id
            JOIN image_types it ON b.image_type_id = it.id
        """
        params = []

        where_clauses = []
        if status:
            where_clauses.append("b.status = ?")
            params.append(status)
        if platform:
            where_clauses.append("p.name = ?")
            params.append(platform)

        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)

        query += " ORDER BY b.created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        builds = conn.execute(query, params).fetchall()
        return [dict(build) for build in builds]

@app.put("/builds/{build_id}")
async def update_build(build_id: str, update: BuildUpdate):
    """Update build metadata"""
    with get_db() as conn:
        # Check if build exists
        build = conn.execute("SELECT id FROM builds WHERE id = ?", (build_id,)).fetchone()
        if not build:
            raise HTTPException(status_code=404, detail="Build not found")

        # Build update query dynamically
        update_fields = []
        params = []
        if update.status:
            update_fields.append("status = ?")
            params.append(update.status)
        if update.ami_id:
            update_fields.append("ami_id = ?")
            params.append(update.ami_id)
        if update.image_id:
            update_fields.append("image_id = ?")
            params.append(update.image_id)
        if update.packer_manifest:
            update_fields.append("packer_manifest = ?")
            params.append(update.packer_manifest)

        if update_fields:
            query = f"UPDATE builds SET {', '.join(update_fields)}, updated_at = ? WHERE id = ?"
            params.extend([datetime.now().isoformat(), build_id])
            conn.execute(query, params)
            conn.commit()

        return {"message": "Build updated successfully"}

# -----------------------------------------------------------------------------
# STATE MANAGEMENT ENDPOINTS
# -----------------------------------------------------------------------------

@app.post("/builds/{build_id}/states")
async def transition_state(build_id: str, transition: StateTransition):
    """Record a state transition"""
    with get_db() as conn:
        # Check if build exists
        build = conn.execute("SELECT id, current_state FROM builds WHERE id = ?", (build_id,)).fetchone()
        if not build:
            raise HTTPException(status_code=404, detail="Build not found")

        now = datetime.now().isoformat()

        # Insert state transition
        conn.execute("""
            INSERT INTO build_states (
                id, build_id, state, status, start_time, end_time, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()), build_id, transition.state, transition.status,
            now, now if transition.status in ['completed', 'failed'] else None,
            transition.error_message
        ))

        # Update build current state and status
        new_status = 'running'
        if transition.status == 'completed' and transition.state == 100:
            new_status = 'completed'
        elif transition.status == 'failed':
            new_status = 'failed'

        conn.execute("""
            UPDATE builds SET
                current_state = ?,
                status = ?,
                updated_at = ?,
                end_time = ?
            WHERE id = ?
        """, (
            transition.state, new_status, now,
            now if new_status in ['completed', 'failed'] else None,
            build_id
        ))

        conn.commit()

        return {"message": f"State transitioned to {transition.state} ({transition.status})"}

@app.get("/builds/{build_id}/states")
async def get_build_states(build_id: str):
    """Get state history for a build"""
    with get_db() as conn:
        states = conn.execute("""
            SELECT state, status, start_time, end_time, duration_seconds, error_message, retry_count
            FROM build_states
            WHERE build_id = ?
            ORDER BY created_at
        """, (build_id,)).fetchall()

        return [dict(state) for state in states]

# -----------------------------------------------------------------------------
# FAILURE MANAGEMENT ENDPOINTS
# -----------------------------------------------------------------------------

@app.post("/builds/{build_id}/failures")
async def record_failure(build_id: str, failure: BuildFailure):
    """Record a build failure"""
    with get_db() as conn:
        # Check if build exists
        build = conn.execute("SELECT id FROM builds WHERE id = ?", (build_id,)).fetchone()
        if not build:
            raise HTTPException(status_code=404, detail="Build not found")

        conn.execute("""
            INSERT INTO build_failures (
                id, build_id, state, failure_type, error_message,
                error_details, component, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()), build_id, failure.state, failure.failure_type,
            failure.error_message, str(failure.error_details) if failure.error_details else None,
            failure.component, datetime.now().isoformat()
        ))

        conn.commit()

        return {"message": "Failure recorded successfully"}

@app.get("/builds/{build_id}/failures")
async def get_build_failures(build_id: str):
    """Get failures for a build"""
    with get_db() as conn:
        failures = conn.execute("""
            SELECT state, failure_type, error_message, component, retry_attempt,
                   created_at, resolved, resolution_notes
            FROM build_failures
            WHERE build_id = ?
            ORDER BY created_at DESC
        """, (build_id,)).fetchall()

        return [dict(failure) for failure in failures]

# -----------------------------------------------------------------------------
# DASHBOARD ENDPOINTS
# -----------------------------------------------------------------------------

@app.get("/dashboard/summary")
async def get_dashboard_summary():
    """Get overall build statistics"""
    with get_db() as conn:
        summary = conn.execute("""
            SELECT
                COUNT(*) as total_builds,
                COUNT(CASE WHEN status = 'running' THEN 1 END) as running,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
                COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed,
                COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending
            FROM builds
        """).fetchone()

        return dict(summary)

@app.get("/dashboard/recent-failures")
async def get_recent_failures(limit: int = 10):
    """Get recent build failures"""
    with get_db() as conn:
        failures = conn.execute("""
            SELECT
                b.build_number,
                b.current_state,
                f.failure_type,
                f.error_message,
                f.component,
                f.created_at,
                p.display_name as platform,
                os.display_name as os_version,
                it.display_name as image_type
            FROM build_failures f
            JOIN builds b ON f.build_id = b.id
            JOIN platforms p ON b.platform_id = p.id
            JOIN os_versions os ON b.os_version_id = os.id
            JOIN image_types it ON b.image_type_id = it.id
            WHERE f.resolved = FALSE
            ORDER BY f.created_at DESC
            LIMIT ?
        """, (limit,)).fetchall()

        return [dict(failure) for failure in failures]

@app.get("/dashboard/running-builds")
async def get_running_builds():
    """Get currently running builds"""
    with get_db() as conn:
        builds = conn.execute("""
            SELECT
                b.build_number,
                b.current_state,
                b.start_time,
                b.concourse_pipeline_url,
                p.display_name as platform,
                os.display_name as os_version,
                it.display_name as image_type
            FROM builds b
            JOIN platforms p ON b.platform_id = p.id
            JOIN os_versions os ON b.os_version_id = os.id
            JOIN image_types it ON b.image_type_id = it.id
            WHERE b.status = 'running'
            ORDER BY b.start_time
        """).fetchall()

        return [dict(build) for build in builds]

# -----------------------------------------------------------------------------
# CONCOURSE INTEGRATION ENDPOINTS
# -----------------------------------------------------------------------------

@app.get("/concourse/resume/{build_number}")
async def get_resume_info(build_number: str):
    """Get information needed to resume a build in Concourse"""
    with get_db() as conn:
        build = conn.execute("""
            SELECT
                b.id, b.build_number, b.current_state, b.status,
                b.concourse_pipeline_url, b.concourse_job_name,
                p.name as platform_name,
                os.name as os_version_name,
                it.name as image_type_name
            FROM builds b
            JOIN platforms p ON b.platform_id = p.id
            JOIN os_versions os ON b.os_version_id = os.id
            JOIN image_types it ON b.image_type_id = it.id
            WHERE b.build_number = ?
        """, (build_number,)).fetchone()

        if not build:
            raise HTTPException(status_code=404, detail="Build not found")

        # Determine resume parameters
        resume_state = build['current_state']
        if build['status'] == 'failed':
            # Stay at failed state for retry
            pass
        elif build['status'] == 'running':
            # Continue to next state
            resume_state = min(resume_state + 5, 100)

        return {
            "build_id": build['id'],
            "build_number": build['build_number'],
            "resume_from_state": resume_state,
            "platform": build['platform_name'],
            "os_version": build['os_version_name'],
            "image_type": build['image_type_name'],
            "concourse_pipeline_url": build['concourse_pipeline_url'],
            "concourse_job_name": build['concourse_job_name']
        }