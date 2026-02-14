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
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deactivated_at TIMESTAMP WITH TIME ZONE,
    FOREIGN KEY (build_id) REFERENCES builds (id)
);

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