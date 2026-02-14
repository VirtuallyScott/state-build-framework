-- Resumable Builds Schema Migration
-- This adds support for tracking build artifacts, variables, and resume operations
-- Run date: February 14, 2026

-- ============================================================================
-- ARTIFACT TRACKING
-- ============================================================================

-- Table: build_artifacts
-- Tracks all artifacts created during a build (snapshots, images, config files)
CREATE TABLE IF NOT EXISTS build_artifacts (
    id TEXT PRIMARY KEY,  -- UUID
    build_id TEXT NOT NULL,
    state_code INTEGER NOT NULL,
    
    -- Artifact identification
    artifact_name TEXT NOT NULL,
    artifact_type TEXT NOT NULL,  -- 'vm_snapshot', 'ami', 'disk_image', 'config_file', etc.
    artifact_path TEXT NOT NULL,         -- Full path/URL to artifact
    
    -- Storage details
    storage_backend TEXT NOT NULL,  -- 's3', 'azure_blob', 'gcp_storage', 'local', 'vsphere'
    storage_region TEXT,
    storage_bucket TEXT,
    storage_key TEXT,                     -- Key/path within bucket
    
    -- Artifact metadata
    size_bytes BIGINT,
    checksum TEXT,                 -- SHA256 checksum
    checksum_algorithm TEXT DEFAULT 'sha256',
    
    -- Artifact lifecycle
    is_resumable BOOLEAN DEFAULT TRUE,    -- Can this artifact be used to resume?
    is_final BOOLEAN DEFAULT FALSE,       -- Is this the final deliverable?
    expires_at TIMESTAMP WITH TIME ZONE,  -- When to clean up temporary artifacts
    
    -- Additional metadata as JSON
    metadata JSONB,                       -- VM ID, snapshot ID, AMI ID, etc.
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE,  -- Soft delete for audit
    
    FOREIGN KEY (build_id) REFERENCES builds(id) ON DELETE CASCADE,
    UNIQUE(build_id, artifact_name)
);

-- Indexes for build_artifacts
CREATE INDEX IF NOT EXISTS idx_build_artifacts_build_id ON build_artifacts(build_id);
CREATE INDEX IF NOT EXISTS idx_build_artifacts_state_code ON build_artifacts(state_code);
CREATE INDEX IF NOT EXISTS idx_build_artifacts_type ON build_artifacts(artifact_type);
CREATE INDEX IF NOT EXISTS idx_build_artifacts_resumable ON build_artifacts(is_resumable) WHERE is_resumable = TRUE;
CREATE INDEX IF NOT EXISTS idx_build_artifacts_expires ON build_artifacts(expires_at) WHERE expires_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_build_artifacts_deleted ON build_artifacts(deleted_at) WHERE deleted_at IS NULL;

-- ============================================================================
-- VARIABLE TRACKING
-- ============================================================================

-- Table: build_variables
-- Stores build-specific variables needed for resumption (VM IDs, network config, etc.)
CREATE TABLE IF NOT EXISTS build_variables (
    id TEXT PRIMARY KEY,  -- UUID
    build_id TEXT NOT NULL,
    
    -- Variable details
    variable_key TEXT NOT NULL,
    variable_value TEXT NOT NULL,
    variable_type TEXT DEFAULT 'string',  -- 'string', 'json', 'encrypted'
    
    -- When was this variable set?
    set_at_state INTEGER,                -- Which state code set this variable
    
    -- Variable lifecycle
    is_sensitive BOOLEAN DEFAULT FALSE,  -- Should this be encrypted/masked?
    is_required_for_resume BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (build_id) REFERENCES builds(id) ON DELETE CASCADE,
    UNIQUE(build_id, variable_key)
);

-- Indexes for build_variables
CREATE INDEX IF NOT EXISTS idx_build_variables_build_id ON build_variables(build_id);
CREATE INDEX IF NOT EXISTS idx_build_variables_required ON build_variables(is_required_for_resume) WHERE is_required_for_resume = TRUE;

-- ============================================================================
-- RESUMABLE STATE CONFIGURATION
-- ============================================================================

-- Table: resumable_states
-- Defines which state codes are resumable and their requirements
CREATE TABLE IF NOT EXISTS resumable_states (
    id TEXT PRIMARY KEY,  -- UUID
    project_id TEXT NOT NULL,
    state_code INTEGER NOT NULL,
    
    -- Resumability configuration
    is_resumable BOOLEAN DEFAULT TRUE,
    resume_strategy TEXT,  -- 'from_artifact', 'rerun_state', 'skip_to_next'
    
    -- Requirements for resumption
    required_artifacts JSONB,     -- Array of artifact names/types needed
    required_variables JSONB,     -- Array of variable keys needed
    
    -- Resume script/command
    resume_command TEXT,          -- Command or script to execute on resume
    resume_timeout_seconds INTEGER DEFAULT 3600,
    
    -- Documentation
    description TEXT,
    notes TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    UNIQUE(project_id, state_code)
);

-- Indexes for resumable_states
CREATE INDEX IF NOT EXISTS idx_resumable_states_project ON resumable_states(project_id);
CREATE INDEX IF NOT EXISTS idx_resumable_states_resumable ON resumable_states(is_resumable) WHERE is_resumable = TRUE;

-- ============================================================================
-- RESUME REQUEST TRACKING
-- ============================================================================

-- Table: resume_requests
-- Tracks requests to resume builds and their status
CREATE TABLE IF NOT EXISTS resume_requests (
    id TEXT PRIMARY KEY,  -- UUID
    build_id TEXT NOT NULL,
    
    -- Resume details
    resume_from_state INTEGER NOT NULL,
    resume_to_state INTEGER,              -- NULL means resume to completion
    resume_reason TEXT,
    
    -- Request source
    requested_by TEXT,            -- User/system that requested resume
    request_source TEXT,           -- 'api', 'webhook', 'cli', 'auto'
    
    -- Orchestration
    orchestration_job_id TEXT,            -- Concourse/Jenkins job ID
    orchestration_job_url TEXT,
    orchestration_status TEXT,     -- 'pending', 'triggered', 'running', 'completed', 'failed'
    
    -- Execution tracking
    triggered_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    
    -- Metadata
    metadata JSONB,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (build_id) REFERENCES builds(id) ON DELETE CASCADE
);

-- Indexes for resume_requests
CREATE INDEX IF NOT EXISTS idx_resume_requests_build_id ON resume_requests(build_id);
CREATE INDEX IF NOT EXISTS idx_resume_requests_status ON resume_requests(orchestration_status);
CREATE INDEX IF NOT EXISTS idx_resume_requests_created ON resume_requests(created_at DESC);

-- ============================================================================
-- BUILD JOB TRACKING
-- ============================================================================

-- Table: build_jobs
-- Links builds to CI/CD job information
CREATE TABLE IF NOT EXISTS build_jobs (
    id TEXT PRIMARY KEY,  -- UUID
    build_id TEXT NOT NULL,
    
    -- CI/CD platform details
    platform TEXT NOT NULL,        -- 'concourse', 'jenkins', 'gitlab-ci', 'github-actions'
    pipeline_name TEXT,
    job_name TEXT NOT NULL,
    job_url TEXT,
    
    -- Job identification
    job_id TEXT,                          -- Platform-specific job ID
    build_number TEXT,
    
    -- Trigger information
    triggered_by TEXT,
    trigger_source TEXT,           -- 'manual', 'webhook', 'schedule', 'resume'
    
    -- Job status
    status TEXT,                   -- 'pending', 'running', 'success', 'failed', 'aborted'
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Resume context
    is_resume_job BOOLEAN DEFAULT FALSE,
    resumed_from_state INTEGER,
    parent_job_id TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (build_id) REFERENCES builds(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_job_id) REFERENCES build_jobs(id) ON DELETE SET NULL
);

-- Indexes for build_jobs
CREATE INDEX IF NOT EXISTS idx_build_jobs_build_id ON build_jobs(build_id);
CREATE INDEX IF NOT EXISTS idx_build_jobs_platform_job ON build_jobs(platform, job_id);
CREATE INDEX IF NOT EXISTS idx_build_jobs_status ON build_jobs(status);
CREATE INDEX IF NOT EXISTS idx_build_jobs_is_resume ON build_jobs(is_resume_job) WHERE is_resume_job = TRUE;

-- ============================================================================
-- UPDATE EXISTING TABLES
-- ============================================================================

-- Add status column to builds table for tracking overall build status
ALTER TABLE builds ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'pending';
ALTER TABLE builds ADD COLUMN IF NOT EXISTS status_message TEXT;

-- Create index on build status
CREATE INDEX IF NOT EXISTS idx_builds_status ON builds(status);

-- ============================================================================
-- SAMPLE DATA FOR TESTING
-- ============================================================================

-- Insert a sample resumable state configuration for the default project
INSERT INTO resumable_states (id, project_id, state_code, is_resumable, resume_strategy, description) VALUES
('resumable-state-20', 'default-project-uuid', 20, TRUE, 'from_artifact', 'Package installation can be resumed from snapshot')
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- VIEWS FOR CONVENIENCE
-- ============================================================================

-- View: build_resume_status
-- Shows builds with their resume capability
CREATE OR REPLACE VIEW build_resume_status AS
SELECT 
    b.id AS build_id,
    b.build_id AS build_number,
    b.status,
    b.platform_id,
    b.project_id,
    COUNT(DISTINCT ba.id) AS artifact_count,
    COUNT(DISTINCT ba.id) FILTER (WHERE ba.is_resumable = TRUE) AS resumable_artifact_count,
    COUNT(DISTINCT bv.id) AS variable_count,
    COUNT(DISTINCT bv.id) FILTER (WHERE bv.is_required_for_resume = TRUE) AS required_variable_count,
    COUNT(DISTINCT rr.id) AS resume_request_count,
    MAX(bs.state_code) AS current_state_code,
    MAX(bs.created_at) AS last_state_change
FROM builds b
LEFT JOIN build_artifacts ba ON b.id = ba.build_id AND ba.deleted_at IS NULL
LEFT JOIN build_variables bv ON b.id = bv.build_id
LEFT JOIN resume_requests rr ON b.id = rr.build_id
LEFT JOIN build_states bs ON b.id = bs.build_id
GROUP BY b.id, b.build_id, b.status, b.platform_id, b.project_id;

-- View: latest_resume_requests
-- Shows the most recent resume request for each build
CREATE OR REPLACE VIEW latest_resume_requests AS
SELECT DISTINCT ON (build_id)
    rr.*
FROM resume_requests rr
ORDER BY build_id, created_at DESC;

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Function: get_resume_context
-- Returns all information needed to resume a build
CREATE OR REPLACE FUNCTION get_resume_context(p_build_id TEXT)
RETURNS JSON AS $$
DECLARE
    result JSON;
BEGIN
    SELECT json_build_object(
        'build', row_to_json(b.*),
        'artifacts', (
            SELECT json_agg(row_to_json(ba.*))
            FROM build_artifacts ba 
            WHERE ba.build_id = p_build_id 
            AND ba.is_resumable = TRUE 
            AND ba.deleted_at IS NULL
        ),
        'variables', (
            SELECT json_object_agg(bv.variable_key, bv.variable_value)
            FROM build_variables bv 
            WHERE bv.build_id = p_build_id
        ),
        'last_state', (
            SELECT MAX(state_code)
            FROM build_states bs
            WHERE bs.build_id = p_build_id
        )
    ) INTO result
    FROM builds b
    WHERE b.id = p_build_id;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Trigger: Update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply update_updated_at trigger to all new tables
CREATE TRIGGER update_build_artifacts_updated_at BEFORE UPDATE ON build_artifacts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_build_variables_updated_at BEFORE UPDATE ON build_variables
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_resumable_states_updated_at BEFORE UPDATE ON resumable_states
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_resume_requests_updated_at BEFORE UPDATE ON resume_requests
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_build_jobs_updated_at BEFORE UPDATE ON build_jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- GRANTS (adjust as needed for your environment)
-- ============================================================================

-- Grant permissions to buildapi user (adjust username as needed)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON build_artifacts TO buildapi;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON build_variables TO buildapi;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON resumable_states TO buildapi;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON resume_requests TO buildapi;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON build_jobs TO buildapi;
-- GRANT SELECT ON build_resume_status TO buildapi;
-- GRANT SELECT ON latest_resume_requests TO buildapi;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- Log migration completion
DO $$
BEGIN
    RAISE NOTICE 'Resumable Builds Migration completed successfully at %', CURRENT_TIMESTAMP;
END
$$;
