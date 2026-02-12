"""
Dashboard and reporting endpoints for the Build State API.
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from typing import List

from ..models import DashboardSummary, RecentBuild
from ..core.auth import get_current_user_or_api_key
from ..core.database import db
from ..dependencies import get_db

router = APIRouter()


@router.get("/dashboard/summary", response_model=DashboardSummary)
async def get_dashboard_summary(
    current_user: dict = Depends(get_current_user_or_api_key),
    db_conn=Depends(get_db)
):
    """Get dashboard summary statistics."""
    # Total builds
    total_query = "SELECT COUNT(*) as count FROM builds"
    total_result = db_conn.execute_query(total_query)
    total_builds = total_result[0]["count"] if total_result else 0

    # Active builds (not completed or failed)
    active_query = "SELECT COUNT(*) as count FROM builds WHERE status = 'running'"
    active_result = db_conn.execute_query(active_query)
    active_builds = active_result[0]["count"] if active_result else 0

    # Completed builds
    completed_query = "SELECT COUNT(*) as count FROM builds WHERE status = 'completed'"
    completed_result = db_conn.execute_query(completed_query)
    completed_builds = completed_result[0]["count"] if completed_result else 0

    # Failed builds
    failed_query = "SELECT COUNT(*) as count FROM builds WHERE status = 'failed'"
    failed_result = db_conn.execute_query(failed_query)
    failed_builds = failed_result[0]["count"] if failed_result else 0

    # Builds by platform
    platform_query = """
    SELECT platform, COUNT(*) as count
    FROM builds
    GROUP BY platform
    """
    platform_results = db_conn.execute_query(platform_query)
    builds_by_platform = {row["platform"]: row["count"] for row in platform_results}

    # Builds by state (group by ranges)
    state_ranges = [
        ("0-9", 0, 9),
        ("10-19", 10, 19),
        ("20-29", 20, 29),
        ("30-39", 30, 39),
        ("40-49", 40, 49),
        ("50-59", 50, 59),
        ("60-69", 60, 69),
        ("70-79", 70, 79),
        ("80-89", 80, 89),
        ("90-99", 90, 99),
        ("100", 100, 100)
    ]

    builds_by_state = {}
    for label, min_state, max_state in state_ranges:
        range_query = f"SELECT COUNT(*) as count FROM builds WHERE current_state BETWEEN {min_state} AND {max_state}"
        range_result = db_conn.execute_query(range_query)
        builds_by_state[label] = range_result[0]["count"] if range_result else 0

    return DashboardSummary(
        total_builds=total_builds,
        active_builds=active_builds,
        completed_builds=completed_builds,
        failed_builds=failed_builds,
        builds_by_platform=builds_by_platform,
        builds_by_state=builds_by_state
    )


@router.get("/dashboard/recent", response_model=List[RecentBuild])
async def get_recent_builds(
    limit: int = 10,
    current_user: dict = Depends(get_current_user_or_api_key),
    db_conn=Depends(get_db)
):
    """Get recently updated builds."""
    query = f"""
    SELECT id, platform, image_type, current_state, status, updated_at
    FROM builds
    ORDER BY updated_at DESC
    LIMIT {limit}
    """

    results = db_conn.execute_query(query)
    return [RecentBuild(**row) for row in results]


@router.get("/dashboard/platform/{platform}")
async def get_platform_dashboard(
    platform: str,
    current_user: dict = Depends(get_current_user_or_api_key),
    db_conn=Depends(get_db)
):
    """Get dashboard data for a specific platform."""
    # Platform statistics
    stats_query = """
    SELECT
        COUNT(*) as total_builds,
        AVG(current_state) as avg_state,
        MIN(updated_at) as oldest_build,
        MAX(updated_at) as newest_build
    FROM builds
    WHERE platform = %s
    """ if db_conn.db_type == "postgresql" else """
    SELECT
        COUNT(*) as total_builds,
        AVG(current_state) as avg_state,
        MIN(updated_at) as oldest_build,
        MAX(updated_at) as newest_build
    FROM builds
    WHERE platform = ?
    """

    stats_result = db_conn.execute_query(stats_query, (platform,))
    stats = stats_result[0] if stats_result else {}

    # Recent builds for this platform
    recent_query = """
    SELECT id, image_type, current_state, status, updated_at
    FROM builds
    WHERE platform = %s
    ORDER BY updated_at DESC
    LIMIT 5
    """ if db_conn.db_type == "postgresql" else """
    SELECT id, image_type, current_state, status, updated_at
    FROM builds
    WHERE platform = ?
    ORDER BY updated_at DESC
    LIMIT 5
    """

    recent_results = db_conn.execute_query(recent_query, (platform,))

    # State distribution
    state_dist_query = """
    SELECT current_state, COUNT(*) as count
    FROM builds
    WHERE platform = %s
    GROUP BY current_state
    ORDER BY current_state
    """ if db_conn.db_type == "postgresql" else """
    SELECT current_state, COUNT(*) as count
    FROM builds
    WHERE platform = ?
    GROUP BY current_state
    ORDER BY current_state
    """

    state_dist = db_conn.execute_query(state_dist_query, (platform,))
    state_distribution = {str(row["current_state"]): row["count"] for row in state_dist}

    return {
        "platform": platform,
        "statistics": stats,
        "recent_builds": recent_results,
        "state_distribution": state_distribution
    }