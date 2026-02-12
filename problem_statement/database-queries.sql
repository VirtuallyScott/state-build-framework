-- Useful Queries for State-Based Build Framework Database

-- =============================================================================
-- DASHBOARD QUERIES
-- =============================================================================

-- Current build status overview
SELECT
    COUNT(*) as total_builds,
    COUNT(CASE WHEN status = 'running' THEN 1 END) as running,
    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed,
    COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending
FROM builds;

-- Builds by platform
SELECT
    p.display_name as platform,
    COUNT(*) as total_builds,
    COUNT(CASE WHEN b.status = 'completed' THEN 1 END) as completed,
    COUNT(CASE WHEN b.status = 'failed' THEN 1 END) as failed,
    COUNT(CASE WHEN b.status = 'running' THEN 1 END) as running
FROM builds b
JOIN platforms p ON b.platform_id = p.id
GROUP BY p.display_name
ORDER BY total_builds DESC;

-- Builds by OS version
SELECT
    os.display_name as os_version,
    COUNT(*) as total_builds,
    COUNT(CASE WHEN b.status = 'completed' THEN 1 END) as completed,
    COUNT(CASE WHEN b.status = 'failed' THEN 1 END) as failed
FROM builds b
JOIN os_versions os ON b.os_version_id = os.id
GROUP BY os.display_name
ORDER BY total_builds DESC;

-- =============================================================================
-- BUILD MONITORING QUERIES
-- =============================================================================

-- Currently running builds
SELECT
    b.build_number,
    p.display_name as platform,
    os.display_name as os_version,
    it.display_name as image_type,
    b.current_state,
    b.start_time,
    ROUND((julianday('now') - julianday(b.start_time)) * 86400) as duration_seconds,
    b.concourse_pipeline_url
FROM builds b
JOIN platforms p ON b.platform_id = p.id
JOIN os_versions os ON b.os_version_id = os.id
JOIN image_types it ON b.image_type_id = it.id
WHERE b.status = 'running'
ORDER BY b.start_time;

-- Failed builds requiring attention
SELECT
    b.build_number,
    p.display_name as platform,
    os.display_name as os_version,
    it.display_name as image_type,
    b.current_state,
    b.start_time,
    COUNT(f.id) as failure_count,
    MAX(f.created_at) as last_failure,
    b.concourse_pipeline_url
FROM builds b
JOIN platforms p ON b.platform_id = p.id
JOIN os_versions os ON b.os_version_id = os.id
JOIN image_types it ON b.image_type_id = it.id
LEFT JOIN build_failures f ON b.id = f.build_id
WHERE b.status = 'failed'
GROUP BY b.id, b.build_number, p.display_name, os.display_name, it.display_name,
         b.current_state, b.start_time, b.concourse_pipeline_url
ORDER BY last_failure DESC;

-- =============================================================================
-- STATE ANALYSIS QUERIES
-- =============================================================================

-- State distribution across all builds
SELECT
    current_state,
    COUNT(*) as builds_at_state,
    COUNT(CASE WHEN status = 'running' THEN 1 END) as running,
    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_stuck_here
FROM builds
GROUP BY current_state
ORDER BY current_state;

-- Most common failure states
SELECT
    state,
    COUNT(*) as failure_count,
    GROUP_CONCAT(DISTINCT failure_type) as failure_types
FROM build_failures
GROUP BY state
ORDER BY failure_count DESC;

-- Average time per state (for completed builds)
SELECT
    bs.state,
    COUNT(*) as transitions,
    AVG(bs.duration_seconds) as avg_duration_seconds,
    MIN(bs.duration_seconds) as min_duration,
    MAX(bs.duration_seconds) as max_duration
FROM build_states bs
WHERE bs.status = 'completed'
GROUP BY bs.state
ORDER BY bs.state;

-- =============================================================================
-- SPECIFIC BUILD QUERIES
-- =============================================================================

-- Get full history for a specific build
SELECT
    b.build_number,
    bs.state,
    bs.status,
    bs.start_time,
    bs.end_time,
    bs.duration_seconds,
    bs.error_message,
    bs.retry_count
FROM builds b
JOIN build_states bs ON b.id = bs.build_id
WHERE b.build_number = 'rhel-8.8-base-aws-commercial-20240212-001'
ORDER BY bs.start_time;

-- Get failures for a specific build
SELECT
    f.state,
    f.failure_type,
    f.error_message,
    f.component,
    f.retry_attempt,
    f.created_at,
    f.resolved,
    f.resolution_notes
FROM build_failures f
JOIN builds b ON f.build_id = b.id
WHERE b.build_number = 'ubuntu-22.04-openvpn-aws-govcloud-20240212-005'
ORDER BY f.created_at;

-- =============================================================================
-- CONCOURSE INTEGRATION QUERIES
-- =============================================================================

-- Builds ready for Concourse pipeline trigger
SELECT
    b.build_number,
    p.name as platform,
    os.name as os_version,
    it.name as image_type,
    b.current_state,
    b.concourse_pipeline_url,
    b.concourse_job_name
FROM builds b
JOIN platforms p ON b.platform_id = p.id
JOIN os_versions os ON b.os_version_id = os.id
JOIN image_types it ON b.image_type_id = it.id
WHERE b.status IN ('pending', 'failed')
ORDER BY b.created_at;

-- Find builds that can resume from specific state
SELECT
    b.build_number,
    b.current_state,
    b.status,
    p.display_name as platform,
    os.display_name as os_version,
    it.display_name as image_type,
    b.concourse_pipeline_url
FROM builds b
JOIN platforms p ON b.platform_id = p.id
JOIN os_versions os ON b.os_version_id = os.id
JOIN image_types it ON b.image_type_id = it.id
WHERE b.current_state = 25  -- Example: resume from state 25
  AND b.status = 'failed'
ORDER BY b.start_time DESC;

-- =============================================================================
-- MAINTENANCE QUERIES
-- =============================================================================

-- Clean up old completed builds (older than 90 days)
SELECT
    'DELETE FROM build_failures WHERE build_id IN (' ||
    GROUP_CONCAT('(SELECT id FROM builds WHERE status = "completed" AND created_at < "' ||
                 datetime('now', '-90 days') || '")')
    || ');' as cleanup_sql;

-- Find builds with excessive failures
SELECT
    b.build_number,
    COUNT(f.id) as failure_count,
    MAX(f.created_at) as last_failure
FROM builds b
JOIN build_failures f ON b.id = f.build_id
GROUP BY b.id, b.build_number
HAVING failure_count > 5
ORDER BY failure_count DESC;

-- =============================================================================
-- REPORTING QUERIES
-- =============================================================================

-- Monthly build success rate
SELECT
    strftime('%Y-%m', created_at) as month,
    COUNT(*) as total_builds,
    COUNT(CASE WHEN status = 'completed' THEN 1 END) as successful,
    ROUND(100.0 * COUNT(CASE WHEN status = 'completed' THEN 1 END) / COUNT(*), 2) as success_rate
FROM builds
WHERE created_at >= datetime('now', '-12 months')
GROUP BY strftime('%Y-%m', created_at)
ORDER BY month DESC;

-- Average build duration by platform
SELECT
    p.display_name as platform,
    COUNT(*) as completed_builds,
    AVG(b.duration_seconds) as avg_duration_seconds,
    AVG(b.duration_seconds) / 60 as avg_duration_minutes
FROM builds b
JOIN platforms p ON b.platform_id = p.id
WHERE b.status = 'completed'
GROUP BY p.display_name
ORDER BY avg_duration_seconds;