-- PostgreSQL initialization script for Build State API
-- Run this when setting up PostgreSQL database

-- Create database and user (run as postgres superuser first)
-- CREATE DATABASE builds;
-- CREATE USER buildapi WITH PASSWORD 'change-this-password';
-- GRANT ALL PRIVILEGES ON DATABASE builds TO buildapi;

-- Switch to builds database and run the following as buildapi user

-- Create tables
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    first_name TEXT,
    last_name TEXT,
    employee_id TEXT,
    hashed_password TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true,
    is_superuser BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deactivated_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS user_profiles (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    employee_id TEXT NOT NULL,
    email TEXT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS api_tokens (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    token_hash TEXT NOT NULL,
    scopes TEXT[], -- Array of permission scopes
    expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deactivated_at TIMESTAMP WITH TIME ZONE,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS platforms (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    cloud_provider TEXT NOT NULL,
    region TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deactivated_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS os_versions (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    version TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deactivated_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS image_types (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deactivated_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS builds (
    id TEXT PRIMARY KEY,
    platform_id TEXT NOT NULL,
    os_version_id TEXT NOT NULL,
    image_type_id TEXT NOT NULL,
    build_id TEXT NOT NULL UNIQUE,
    pipeline_url TEXT,
    commit_hash TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deactivated_at TIMESTAMP WITH TIME ZONE,
    FOREIGN KEY (platform_id) REFERENCES platforms (id),
    FOREIGN KEY (os_version_id) REFERENCES os_versions (id),
    FOREIGN KEY (image_type_id) REFERENCES image_types (id)
);

CREATE TABLE IF NOT EXISTS build_states (
    id SERIAL PRIMARY KEY,
    build_id TEXT NOT NULL,
    state_code INTEGER NOT NULL,
    message TEXT,
    artifact_storage_type VARCHAR(50),
    artifact_storage_path TEXT,
    artifact_size_bytes BIGINT,
    artifact_checksum VARCHAR(128),
    artifact_metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deactivated_at TIMESTAMP WITH TIME ZONE,
    FOREIGN KEY (build_id) REFERENCES builds (id)
);

-- Indexes for build_states table
CREATE INDEX IF NOT EXISTS idx_build_states_artifact_storage_type ON build_states(artifact_storage_type);
CREATE INDEX IF NOT EXISTS idx_build_states_build_id_state ON build_states(build_id, state_code);

CREATE TABLE IF NOT EXISTS build_failures (
    id SERIAL PRIMARY KEY,
    build_id TEXT NOT NULL,
    error_message TEXT NOT NULL,
    error_code TEXT,
    component TEXT,
    details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deactivated_at TIMESTAMP WITH TIME ZONE,
    FOREIGN KEY (build_id) REFERENCES builds (id)
);

-- ============================================================================
-- RESUMABLE BUILDS TABLES
-- ============================================================================

-- Table: build_artifacts
-- Tracks all artifacts created during a build (snapshots, images, config files)
CREATE TABLE IF NOT EXISTS build_artifacts (
    id TEXT PRIMARY KEY,
    build_id TEXT NOT NULL,
    state_code INTEGER NOT NULL,
    
    -- Artifact identification
    artifact_name TEXT NOT NULL,
    artifact_type TEXT NOT NULL,
    artifact_path TEXT NOT NULL,
    
    -- Storage details
    storage_backend TEXT NOT NULL,
    storage_region TEXT,
    storage_bucket TEXT,
    storage_key TEXT,
    
    -- Artifact metadata
    size_bytes BIGINT,
    checksum TEXT,
    checksum_algorithm TEXT DEFAULT 'sha256',
    
    -- Artifact lifecycle
    is_resumable BOOLEAN DEFAULT TRUE,
    is_final BOOLEAN DEFAULT FALSE,
    expires_at TIMESTAMP WITH TIME ZONE,
    
    -- Additional metadata as JSON
    metadata JSONB,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
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

-- Table: build_variables
-- Stores build-specific variables needed for resumption
CREATE TABLE IF NOT EXISTS build_variables (
    id TEXT PRIMARY KEY,
    build_id TEXT NOT NULL,
    
    -- Variable details
    variable_key TEXT NOT NULL,
    variable_value TEXT NOT NULL,
    variable_type TEXT DEFAULT 'string',
    
    -- When was this variable set?
    set_at_state INTEGER,
    
    -- Variable lifecycle
    is_sensitive BOOLEAN DEFAULT FALSE,
    is_required_for_resume BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (build_id) REFERENCES builds(id) ON DELETE CASCADE,
    UNIQUE(build_id, variable_key)
);

-- Indexes for build_variables
CREATE INDEX IF NOT EXISTS idx_build_variables_build_id ON build_variables(build_id);
CREATE INDEX IF NOT EXISTS idx_build_variables_required ON build_variables(is_required_for_resume) WHERE is_required_for_resume = TRUE;

-- Table: resumable_states
-- Defines which state codes are resumable and their requirements
CREATE TABLE IF NOT EXISTS resumable_states (
    id TEXT PRIMARY KEY,
    project_id TEXT,
    state_code INTEGER NOT NULL,
    
    -- Resumability configuration
    is_resumable BOOLEAN DEFAULT TRUE,
    resume_strategy TEXT,
    
    -- Requirements for resumption
    required_artifacts JSONB,
    required_variables JSONB,
    
    -- Resume script/command
    resume_command TEXT,
    resume_timeout_seconds INTEGER DEFAULT 3600,
    
    -- Documentation
    description TEXT,
    notes TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for resumable_states
CREATE INDEX IF NOT EXISTS idx_resumable_states_resumable ON resumable_states(is_resumable) WHERE is_resumable = TRUE;

-- Table: resume_requests
-- Tracks requests to resume builds and their status
CREATE TABLE IF NOT EXISTS resume_requests (
    id TEXT PRIMARY KEY,
    build_id TEXT NOT NULL,
    
    -- Resume details
    resume_from_state INTEGER NOT NULL,
    resume_to_state INTEGER,
    resume_reason TEXT,
    
    -- Request source
    requested_by TEXT,
    request_source TEXT,
    
    -- Orchestration
    orchestration_job_id TEXT,
    orchestration_job_url TEXT,
    orchestration_status TEXT,
    
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

-- Table: build_jobs
-- Links builds to CI/CD job information
CREATE TABLE IF NOT EXISTS build_jobs (
    id TEXT PRIMARY KEY,
    build_id TEXT NOT NULL,
    
    -- CI/CD platform details
    platform TEXT NOT NULL,
    pipeline_name TEXT,
    job_name TEXT NOT NULL,
    job_url TEXT,
    
    -- Job identification
    job_id TEXT,
    build_number TEXT,
    
    -- Trigger information
    triggered_by TEXT,
    trigger_source TEXT,
    
    -- Job status
    status TEXT,
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

CREATE TABLE IF NOT EXISTS api_keys (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    key_hash TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    active BOOLEAN DEFAULT true,
    deactivated_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_profiles_employee_id ON user_profiles(employee_id);
CREATE INDEX IF NOT EXISTS idx_api_tokens_user_id ON api_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_api_tokens_active ON api_tokens(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_builds_build_id ON builds(build_id);
CREATE INDEX IF NOT EXISTS idx_build_states_build_id ON build_states(build_id);
CREATE INDEX IF NOT EXISTS idx_build_failures_build_id ON build_failures(build_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_active ON api_keys(active) WHERE active = true;

-- Insert sample data
INSERT INTO users (id, username, email, first_name, last_name, employee_id, hashed_password, is_active, is_superuser) VALUES
('admin-user', 'admin', 'admin@company.com', 'Admin', 'User', 'EMP001', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeCt1uB0YwBqXs.3e', true, true),
('test-user', 'testuser', 'test@company.com', 'Test', 'User', 'EMP002', '$2b$12$C6s5n/PeB0diECBZ0IO1WuDMuCkMPwURbS3ZKGxlaOFI193gin82u', true, false)
ON CONFLICT (id) DO NOTHING;

INSERT INTO user_profiles (id, user_id, first_name, last_name, employee_id, email, start_date) VALUES
('admin-profile', 'admin-user', 'Admin', 'User', 'EMP001', 'admin@company.com', '2024-01-01'),
('test-profile', 'test-user', 'Test', 'User', 'EMP002', 'test@company.com', '2024-01-01')
ON CONFLICT (id) DO NOTHING;

INSERT INTO api_tokens (id, user_id, name, token_hash, scopes) VALUES
('admin-token', 'admin-user', 'Admin Token', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeCt1uB0YwBqXs.3e', ARRAY['read', 'write', 'admin']),
('test-token', 'test-user', 'Test Token', '$2b$12$rHr37bE5MMVL0XeMmawHve6MmDT7cQEqiWlxupOgtFAhi9bpAUcna', ARRAY['read', 'write'])
ON CONFLICT (id) DO NOTHING;

INSERT INTO platforms (id, name, cloud_provider, region) VALUES
('aws-commercial', 'AWS Commercial', 'aws', 'us-east-1'),
('aws-govcloud', 'AWS GovCloud', 'aws', 'us-gov-east-1'),
('azure', 'Azure Commercial', 'azure', 'eastus'),
('gcp', 'Google Cloud Platform', 'gcp', 'us-central1'),
('openstack', 'OpenStack', 'openstack', 'region1')
ON CONFLICT (id) DO NOTHING;

INSERT INTO os_versions (id, name, version) VALUES
('rhel-8.8', 'Red Hat Enterprise Linux', '8.8'),
('rhel-9.2', 'Red Hat Enterprise Linux', '9.2'),
('ubuntu-20.04', 'Ubuntu', '20.04'),
('ubuntu-22.04', 'Ubuntu', '22.04')
ON CONFLICT (id) DO NOTHING;

INSERT INTO image_types (id, name, description) VALUES
('base', 'Base Image', 'Basic OS installation'),
('hana', 'SAP HANA', 'SAP HANA optimized image'),
('sapapp', 'SAP Application', 'SAP application server image'),
('openvpn', 'OpenVPN', 'VPN server image')
ON CONFLICT (id) DO NOTHING;

-- Insert sample API key (hash of 'dev-key-12345')
INSERT INTO api_keys (id, name, key_hash) VALUES
('dev-key', 'Development Key', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeCt1uB0YwBqXs.3e')
ON CONFLICT (id) DO NOTHING;