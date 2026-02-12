-- State-Based Build Framework Database Schema
-- Compatible with SQLite and PostgreSQL
-- Uses UUID for primary keys, ISO UTC timestamps

-- Enable foreign keys in SQLite
PRAGMA foreign_keys = ON;

-- Platforms table (Azure, AWS, GCP, etc.)
CREATE TABLE platforms (
    id TEXT PRIMARY KEY,  -- UUID
    name TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    cloud_provider TEXT NOT NULL,  -- 'azure', 'aws', 'gcp', 'openstack', 'cloudfoundry'
    region TEXT,  -- Optional region specification
    created_at TEXT NOT NULL DEFAULT (datetime('now')),  -- ISO UTC
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- OS Versions table (RHEL 8.8, SLES 15, Ubuntu 20, etc.)
CREATE TABLE os_versions (
    id TEXT PRIMARY KEY,  -- UUID
    name TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    os_family TEXT NOT NULL,  -- 'rhel', 'sles', 'ubuntu'
    major_version INTEGER NOT NULL,
    minor_version INTEGER,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Image Types table (Base, HANA, SAPAPP, OpenVPN, etc.)
CREATE TABLE image_types (
    id TEXT PRIMARY KEY,  -- UUID
    name TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    description TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Builds table (main build records)
CREATE TABLE builds (
    id TEXT PRIMARY KEY,  -- UUID
    build_number TEXT NOT NULL UNIQUE,  -- e.g., 'rhel-8.8-base-aws-commercial-20240212-001'
    platform_id TEXT NOT NULL,
    os_version_id TEXT NOT NULL,
    image_type_id TEXT NOT NULL,
    current_state INTEGER NOT NULL DEFAULT 0,  -- 0-100
    status TEXT NOT NULL DEFAULT 'pending',  -- 'pending', 'running', 'completed', 'failed', 'cancelled'
    start_time TEXT,  -- ISO UTC timestamp
    end_time TEXT,  -- ISO UTC timestamp
    duration_seconds INTEGER,  -- Computed field
    concourse_pipeline_url TEXT,  -- Link to Concourse pipeline
    concourse_job_name TEXT,
    ami_id TEXT,  -- For AWS AMIs
    image_id TEXT,  -- For Azure/GCP images
    packer_manifest TEXT,  -- JSON manifest from Packer
    created_by TEXT,  -- User who triggered the build
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),

    FOREIGN KEY (platform_id) REFERENCES platforms(id),
    FOREIGN KEY (os_version_id) REFERENCES os_versions(id),
    FOREIGN KEY (image_type_id) REFERENCES image_types(id)
);

-- Build States History table (state transitions)
CREATE TABLE build_states (
    id TEXT PRIMARY KEY,  -- UUID
    build_id TEXT NOT NULL,
    state INTEGER NOT NULL,  -- 0-100
    status TEXT NOT NULL,  -- 'started', 'completed', 'failed', 'skipped'
    start_time TEXT NOT NULL,  -- ISO UTC
    end_time TEXT,  -- ISO UTC
    duration_seconds INTEGER,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),

    FOREIGN KEY (build_id) REFERENCES builds(id)
);

-- Build Failures table (detailed failure tracking)
CREATE TABLE build_failures (
    id TEXT PRIMARY KEY,  -- UUID
    build_id TEXT NOT NULL,
    state INTEGER NOT NULL,
    failure_type TEXT NOT NULL,  -- 'packer_error', 'ansible_error', 'network_error', 'validation_error'
    error_message TEXT NOT NULL,
    error_details TEXT,  -- JSON with stack traces, logs, etc.
    component TEXT,  -- 'packer', 'ansible', 'concourse', 'aws_api', etc.
    retry_attempt INTEGER DEFAULT 1,
    resolved BOOLEAN DEFAULT FALSE,
    resolution_notes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    resolved_at TEXT,

    FOREIGN KEY (build_id) REFERENCES builds(id)
);

-- Indexes for performance
CREATE INDEX idx_builds_platform_os_image ON builds(platform_id, os_version_id, image_type_id);
CREATE INDEX idx_builds_status ON builds(status);
CREATE INDEX idx_builds_created_at ON builds(created_at);
CREATE INDEX idx_build_states_build_id ON build_states(build_id);
CREATE INDEX idx_build_states_state ON build_states(state);
CREATE INDEX idx_build_failures_build_id ON build_failures(build_id);
CREATE INDEX idx_build_failures_unresolved ON build_failures(resolved) WHERE resolved = FALSE;

-- Views for common queries
CREATE VIEW build_summary AS
SELECT
    b.id,
    b.build_number,
    p.display_name as platform,
    os.display_name as os_version,
    it.display_name as image_type,
    b.current_state,
    b.status,
    b.start_time,
    b.end_time,
    b.duration_seconds,
    b.concourse_pipeline_url,
    b.created_by,
    COUNT(bs.id) as total_state_changes,
    COUNT(CASE WHEN bs.status = 'failed' THEN 1 END) as failed_states,
    MAX(bs.created_at) as last_state_change
FROM builds b
JOIN platforms p ON b.platform_id = p.id
JOIN os_versions os ON b.os_version_id = os.id
JOIN image_types it ON b.image_type_id = it.id
LEFT JOIN build_states bs ON b.id = bs.build_id
GROUP BY b.id, b.build_number, p.display_name, os.display_name, it.display_name,
         b.current_state, b.status, b.start_time, b.end_time, b.duration_seconds,
         b.concourse_pipeline_url, b.created_by;

CREATE VIEW current_build_status AS
SELECT
    b.build_number,
    p.name as platform,
    os.name as os_version,
    it.name as image_type,
    b.current_state,
    b.status,
    bs.status as current_state_status,
    bs.start_time as state_start_time,
    CASE
        WHEN b.status = 'running' THEN datetime('now', bs.start_time, 'utc')
        ELSE bs.duration_seconds || ' seconds'
    END as time_in_current_state,
    b.concourse_pipeline_url
FROM builds b
JOIN platforms p ON b.platform_id = p.id
JOIN os_versions os ON b.os_version_id = os.id
JOIN image_types it ON b.image_type_id = it.id
LEFT JOIN build_states bs ON b.id = bs.build_id
    AND bs.id = (
        SELECT id FROM build_states
        WHERE build_id = b.id
        ORDER BY created_at DESC LIMIT 1
    );