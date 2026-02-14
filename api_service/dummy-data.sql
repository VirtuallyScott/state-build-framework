-- Dummy data for development environment
-- This file contains sample data for testing and development
-- Only loaded when ENVIRONMENT=development

-- Additional users
INSERT INTO users (id, username, email, first_name, last_name, employee_id, hashed_password, is_active, is_superuser) VALUES
('user-001', 'alice', 'alice@company.com', 'Alice', 'Johnson', 'EMP003', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeCt1uB0YwBqXs.3e', true, false),
('user-002', 'bob', 'bob@company.com', 'Bob', 'Smith', 'EMP004', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeCt1uB0YwBqXs.3e', true, false),
('user-003', 'charlie', 'charlie@company.com', 'Charlie', 'Brown', 'EMP005', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeCt1uB0YwBqXs.3e', true, false),
('user-004', 'diana', 'diana@company.com', 'Diana', 'Prince', 'EMP006', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeCt1uB0YwBqXs.3e', false, false)
ON CONFLICT (id) DO NOTHING;

-- Additional user profiles
INSERT INTO user_profiles (id, user_id, first_name, last_name, employee_id, email, start_date, end_date) VALUES
('profile-001', 'user-001', 'Alice', 'Johnson', 'EMP003', 'alice@company.com', '2024-02-01', NULL),
('profile-002', 'user-002', 'Bob', 'Smith', 'EMP004', 'bob@company.com', '2024-03-01', NULL),
('profile-003', 'user-003', 'Charlie', 'Brown', 'EMP005', 'charlie@company.com', '2024-01-15', NULL),
('profile-004', 'user-004', 'Diana', 'Prince', 'EMP006', 'diana@company.com', '2024-04-01', '2024-12-31')
ON CONFLICT (id) DO NOTHING;

-- Additional API tokens
INSERT INTO api_tokens (id, user_id, name, token_hash, scopes, expires_at) VALUES
('token-001', 'user-001', 'Alice Token', 'dev-api-key-12345', ARRAY['read', 'write'], '2025-12-31 23:59:59+00'),
('token-002', 'user-002', 'Bob Token', 'bob-token-67890', ARRAY['read'], NULL),
('token-003', 'user-003', 'Charlie Token', 'charlie-token-abcde', ARRAY['read', 'write', 'admin'], NULL)
ON CONFLICT (id) DO NOTHING;

-- Additional platforms
INSERT INTO platforms (id, name, cloud_provider, region) VALUES
('aws-china', 'AWS China', 'aws', 'cn-north-1'),
('azure-gov', 'Azure Government', 'azure', 'usgovvirginia'),
('gcp-europe', 'Google Cloud Europe', 'gcp', 'europe-west1'),
('oci', 'Oracle Cloud', 'oci', 'us-ashburn-1')
ON CONFLICT (id) DO NOTHING;

-- Additional OS versions
INSERT INTO os_versions (id, name, version) VALUES
('rhel-8.9', 'Red Hat Enterprise Linux', '8.9'),
('rhel-9.3', 'Red Hat Enterprise Linux', '9.3'),
('ubuntu-22.10', 'Ubuntu', '22.10'),
('ubuntu-23.04', 'Ubuntu', '23.04'),
('centos-7', 'CentOS', '7.9'),
('sles-15', 'SUSE Linux Enterprise Server', '15.4')
ON CONFLICT (id) DO NOTHING;

-- Additional image types
INSERT INTO image_types (id, name, description) VALUES
('webserver', 'Web Server', 'Apache/Nginx web server image'),
('database', 'Database Server', 'MySQL/PostgreSQL database server'),
('cache', 'Cache Server', 'Redis/Memcached cache server'),
('monitoring', 'Monitoring', 'Prometheus/Grafana monitoring stack'),
('security', 'Security Tools', 'Various security scanning tools')
ON CONFLICT (id) DO NOTHING;

-- Sample builds
INSERT INTO builds (id, platform_id, os_version_id, image_type_id, build_id, pipeline_url, commit_hash) VALUES
('build-001', 'aws-commercial', 'rhel-8.8', 'base', 'BUILD-2024-001', 'https://pipeline.company.com/builds/12345', 'a1b2c3d4e5f6'),
('build-002', 'aws-commercial', 'ubuntu-20.04', 'hana', 'BUILD-2024-002', 'https://pipeline.company.com/builds/12346', 'f6e5d4c3b2a1'),
('build-003', 'azure', 'rhel-9.2', 'sapapp', 'BUILD-2024-003', 'https://pipeline.company.com/builds/12347', '1a2b3c4d5e6f'),
('build-004', 'gcp', 'ubuntu-22.04', 'base', 'BUILD-2024-004', 'https://pipeline.company.com/builds/12348', '6f5e4d3c2b1a'),
('build-005', 'aws-govcloud', 'rhel-8.8', 'openvpn', 'BUILD-2024-005', 'https://pipeline.company.com/builds/12349', 'abcdef123456'),
('build-006', 'aws-commercial', 'ubuntu-20.04', 'webserver', 'BUILD-2024-006', 'https://pipeline.company.com/builds/12350', '654321fedcba'),
('build-007', 'azure', 'rhel-9.2', 'database', 'BUILD-2024-007', 'https://pipeline.company.com/builds/12351', 'fedcba654321'),
('build-008', 'gcp', 'ubuntu-22.04', 'cache', 'BUILD-2024-008', 'https://pipeline.company.com/builds/12352', '123456abcdef'),
('build-009', 'aws-commercial', 'centos-7', 'monitoring', 'BUILD-2024-009', 'https://pipeline.company.com/builds/12353', 'abcdef654321'),
('build-010', 'azure', 'sles-15', 'security', 'BUILD-2024-010', 'https://pipeline.company.com/builds/12354', '654321abcdef')
ON CONFLICT DO NOTHING;

-- Build states (state codes: 0=pending, 1=running, 2=success, 3=failed, 4=cancelled)
INSERT INTO build_states (build_id, state_code, message) VALUES
('build-001', 2, 'Build completed successfully'),
('build-002', 2, 'SAP HANA installation completed'),
('build-003', 3, 'Failed during SAP application deployment'),
('build-004', 2, 'Base image creation successful'),
('build-005', 1, 'OpenVPN configuration in progress'),
('build-006', 2, 'Web server setup completed'),
('build-007', 3, 'Database installation failed - insufficient memory'),
('build-008', 2, 'Redis cache server ready'),
('build-009', 0, 'Build queued'),
('build-010', 4, 'Build cancelled by user')
ON CONFLICT DO NOTHING;

-- Build failures (for failed builds)
INSERT INTO build_failures (build_id, error_message, error_code, component, details) VALUES
('build-003', 'SAP application deployment failed due to missing dependencies', 'SAP_DEPLOY_001', 'sap-deployment', '{"phase": "application-install", "error_type": "dependency_missing", "packages": ["sapjco3", "saprouter"]}'),
('build-007', 'Database server installation failed - out of memory', 'DB_INSTALL_001', 'database-setup', '{"phase": "memory_allocation", "required_memory": "16GB", "available_memory": "8GB"}')
ON CONFLICT DO NOTHING;

-- Additional API keys
INSERT INTO api_keys (id, name, key_hash, expires_at, active) VALUES
('ci-key', 'CI/CD Pipeline Key', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeCt1uB0YwBqXs.3e', '2025-06-30 23:59:59+00', true),
('test-key', 'Testing Key', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeCt1uB0YwBqXs.3e', NULL, true),
('expired-key', 'Expired Key', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeCt1uB0YwBqXs.3e', '2024-01-01 00:00:00+00', false)
ON CONFLICT (id) DO NOTHING;