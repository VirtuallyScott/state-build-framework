-- Sample Data for State-Based Build Framework
-- This populates the database with realistic build scenarios

-- Insert Platforms
INSERT INTO platforms (id, name, display_name, cloud_provider, region) VALUES
('550e8400-e29b-41d4-a716-446655440001', 'azure', 'Azure Commercial', 'azure', 'eastus'),
('550e8400-e29b-41d4-a716-446655440002', 'aws-commercial', 'AWS Commercial', 'aws', 'us-east-1'),
('550e8400-e29b-41d4-a716-446655440003', 'aws-govcloud', 'AWS GovCloud', 'aws', 'us-gov-east-1'),
('550e8400-e29b-41d4-a716-446655440004', 'gcp', 'Google Cloud Platform', 'gcp', 'us-central1'),
('550e8400-e29b-41d4-a716-446655440005', 'openstack', 'OpenStack (On-Premise)', 'openstack', 'datacenter-1'),
('550e8400-e29b-41d4-a716-446655440006', 'cloudfoundry', 'Cloud Foundry Stem Cells', 'cloudfoundry', NULL);

-- Insert OS Versions
INSERT INTO os_versions (id, name, display_name, os_family, major_version, minor_version) VALUES
('660e8400-e29b-41d4-a716-446655440001', 'rhel-8.8', 'RHEL 8.8', 'rhel', 8, 8),
('660e8400-e29b-41d4-a716-446655440002', 'rhel-8.10', 'RHEL 8.10', 'rhel', 8, 10),
('660e8400-e29b-41d4-a716-446655440003', 'rhel-9.2', 'RHEL 9.2', 'rhel', 9, 2),
('660e8400-e29b-41d4-a716-446655440004', 'rhel-9.6', 'RHEL 9.6', 'rhel', 9, 6),
('660e8400-e29b-41d4-a716-446655440005', 'sles-15', 'SLES 15', 'sles', 15, NULL),
('660e8400-e29b-41d4-a716-446655440006', 'sles-15.6', 'SLES 15 SP6', 'sles', 15, 6),
('660e8400-e29b-41d4-a716-446655440007', 'sles-15.7', 'SLES 15 SP7', 'sles', 15, 7),
('660e8400-e29b-41d4-a716-446655440008', 'ubuntu-20.04', 'Ubuntu 20.04 LTS', 'ubuntu', 20, 4),
('660e8400-e29b-41d4-a716-446655440009', 'ubuntu-22.04', 'Ubuntu 22.04 LTS', 'ubuntu', 22, 4),
('660e8400-e29b-41d4-a716-446655440010', 'ubuntu-24.04', 'Ubuntu 24.04 LTS', 'ubuntu', 24, 4);

-- Insert Image Types
INSERT INTO image_types (id, name, display_name, description) VALUES
('770e8400-e29b-41d4-a716-446655440001', 'base', 'Base Image', 'Minimal OS installation with basic configuration'),
('770e8400-e29b-41d4-a716-446655440002', 'hana', 'SAP HANA', 'Optimized for SAP HANA database workloads'),
('770e8400-e29b-41d4-a716-446655440003', 'sapapp', 'SAP Application', 'Optimized for SAP application servers'),
('770e8400-e29b-41d4-a716-446655440004', 'openvpn', 'OpenVPN Server', 'VPN server configuration for secure access');

-- Insert Sample Builds with different states
INSERT INTO builds (id, build_number, platform_id, os_version_id, image_type_id, current_state, status, start_time, end_time, duration_seconds, concourse_pipeline_url, concourse_job_name, ami_id, created_by) VALUES
-- Completed builds
('880e8400-e29b-41d4-a716-446655440001', 'rhel-8.8-base-aws-commercial-20240212-001', '550e8400-e29b-41d4-a716-446655440002', '660e8400-e29b-41d4-a716-446655440001', '770e8400-e29b-41d4-a716-446655440001', 100, 'completed', '2024-02-12T08:00:00Z', '2024-02-12T09:15:00Z', 4500, 'https://concourse.example.com/teams/main/pipelines/image-builds/jobs/build-aws-commercial', 'build-aws-commercial', 'ami-1234567890abcdef0', 'john.doe@sap.com'),
('880e8400-e29b-41d4-a716-446655440002', 'rhel-8.8-hana-azure-20240212-002', '550e8400-e29b-41d4-a716-446655440001', '660e8400-e29b-41d4-a716-446655440001', '770e8400-e29b-41d4-a716-446655440002', 100, 'completed', '2024-02-12T09:00:00Z', '2024-02-12T10:45:00Z', 6300, 'https://concourse.example.com/teams/main/pipelines/image-builds/jobs/build-azure', 'build-azure', NULL, 'jane.smith@sap.com'),

-- Running builds at different states
('880e8400-e29b-41d4-a716-446655440003', 'rhel-9.2-base-gcp-20240212-003', '550e8400-e29b-41d4-a716-446655440004', '660e8400-e29b-41d4-a716-446655440003', '770e8400-e29b-41d4-a716-446655440001', 45, 'running', '2024-02-12T10:30:00Z', NULL, NULL, 'https://concourse.example.com/teams/main/pipelines/image-builds/jobs/build-gcp', 'build-gcp', NULL, 'bob.wilson@sap.com'),
('880e8400-e29b-41d4-a716-446655440004', 'sles-15.6-sapapp-openstack-20240212-004', '550e8400-e29b-41d4-a716-446655440005', '660e8400-e29b-41d4-a716-446655440006', '770e8400-e29b-41d4-a716-446655440003', 70, 'running', '2024-02-12T11:00:00Z', NULL, NULL, 'https://concourse.example.com/teams/main/pipelines/image-builds/jobs/build-openstack', 'build-openstack', NULL, 'alice.jones@sap.com'),

-- Failed builds at different states
('880e8400-e29b-41d4-a716-446655440005', 'ubuntu-22.04-openvpn-aws-govcloud-20240212-005', '550e8400-e29b-41d4-a716-446655440003', '660e8400-e29b-41d4-a716-446655440009', '770e8400-e29b-41d4-a716-446655440004', 25, 'failed', '2024-02-12T12:00:00Z', '2024-02-12T12:30:00Z', 1800, 'https://concourse.example.com/teams/main/pipelines/image-builds/jobs/build-aws-govcloud', 'build-aws-govcloud', NULL, 'charlie.brown@sap.com'),
('880e8400-e29b-41d4-a716-446655440006', 'rhel-8.10-base-cloudfoundry-20240212-006', '550e8400-e29b-41d4-a716-446655440006', '660e8400-e29b-41d4-a716-446655440002', '770e8400-e29b-41d4-a716-446655440001', 10, 'failed', '2024-02-12T13:00:00Z', '2024-02-12T13:05:00Z', 300, 'https://concourse.example.com/teams/main/pipelines/image-builds/jobs/build-cloudfoundry', 'build-cloudfoundry', NULL, 'diana.prince@sap.com'),

-- Builds at various early states
('880e8400-e29b-41d4-a716-446655440007', 'sles-15.7-hana-aws-commercial-20240212-007', '550e8400-e29b-41d4-a716-446655440002', '660e8400-e29b-41d4-a716-446655440007', '770e8400-e29b-41d4-a716-446655440002', 5, 'running', '2024-02-12T14:00:00Z', NULL, NULL, 'https://concourse.example.com/teams/main/pipelines/image-builds/jobs/build-aws-commercial', 'build-aws-commercial', NULL, 'eve.adams@sap.com'),
('880e8400-e29b-41d4-a716-446655440008', 'ubuntu-24.04-sapapp-azure-20240212-008', '550e8400-e29b-41d4-a716-446655440001', '660e8400-e29b-41d4-a716-446655440010', '770e8400-e29b-41d4-a716-446655440003', 15, 'running', '2024-02-12T14:30:00Z', NULL, NULL, 'https://concourse.example.com/teams/main/pipelines/image-builds/jobs/build-azure', 'build-azure', NULL, 'frank.miller@sap.com');

-- Insert Build States History
INSERT INTO build_states (id, build_id, state, status, start_time, end_time, duration_seconds, error_message, retry_count) VALUES
-- Completed build state transitions
('990e8400-e29b-41d4-a716-446655440001', '880e8400-e29b-41d4-a716-446655440001', 0, 'started', '2024-02-12T08:00:00Z', '2024-02-12T08:00:05Z', 5, NULL, 0),
('990e8400-e29b-41d4-a716-446655440002', '880e8400-e29b-41d4-a716-446655440001', 5, 'completed', '2024-02-12T08:00:05Z', '2024-02-12T08:15:05Z', 900, NULL, 0),
('990e8400-e29b-41d4-a716-446655440003', '880e8400-e29b-41d4-a716-446655440001', 10, 'completed', '2024-02-12T08:15:05Z', '2024-02-12T08:25:05Z', 600, NULL, 0),
('990e8400-e29b-41d4-a716-446655440004', '880e8400-e29b-41d4-a716-446655440001', 15, 'completed', '2024-02-12T08:25:05Z', '2024-02-12T08:35:05Z', 600, NULL, 0),
('990e8400-e29b-41d4-a716-446655440005', '880e8400-e29b-41d4-a716-446655440001', 20, 'completed', '2024-02-12T08:35:05Z', '2024-02-12T08:45:05Z', 600, NULL, 0),
('990e8400-e29b-41d4-a716-446655440006', '880e8400-e29b-41d4-a716-446655440001', 25, 'completed', '2024-02-12T08:45:05Z', '2024-02-12T08:55:05Z', 600, NULL, 0),
('990e8400-e29b-41d4-a716-446655440007', '880e8400-e29b-41d4-a716-446655440001', 30, 'completed', '2024-02-12T08:55:05Z', '2024-02-12T09:05:05Z', 600, NULL, 0),
('990e8400-e29b-41d4-a716-446655440008', '880e8400-e29b-41d4-a716-446655440001', 35, 'completed', '2024-02-12T09:05:05Z', '2024-02-12T09:15:05Z', 600, NULL, 0),
('990e8400-e29b-41d4-a716-446655440009', '880e8400-e29b-41d4-a716-446655440001', 100, 'completed', '2024-02-12T09:15:05Z', '2024-02-12T09:15:00Z', 0, NULL, 0),

-- Failed build with retries
('990e8400-e29b-41d4-a716-446655440010', '880e8400-e29b-41d4-a716-446655440005', 0, 'started', '2024-02-12T12:00:00Z', '2024-02-12T12:00:05Z', 5, NULL, 0),
('990e8400-e29b-41d4-a716-446655440011', '880e8400-e29b-41d4-a716-446655440005', 5, 'completed', '2024-02-12T12:00:05Z', '2024-02-12T12:15:05Z', 900, NULL, 0),
('990e8400-e29b-41d4-a716-446655440012', '880e8400-e29b-41d4-a716-446655440005', 10, 'completed', '2024-02-12T12:15:05Z', '2024-02-12T12:20:05Z', 300, NULL, 0),
('990e8400-e29b-41d4-a716-446655440013', '880e8400-e29b-41d4-a716-446655440005', 15, 'completed', '2024-02-12T12:20:05Z', '2024-02-12T12:25:05Z', 300, NULL, 0),
('990e8400-e29b-41d4-a716-446655440014', '880e8400-e29b-41d4-a716-446655440005', 20, 'completed', '2024-02-12T12:25:05Z', '2024-02-12T12:27:05Z', 120, NULL, 0),
('990e8400-e29b-41d4-a716-446655440015', '880e8400-e29b-41d4-a716-446655440005', 25, 'failed', '2024-02-12T12:27:05Z', '2024-02-12T12:30:05Z', 180, 'Ansible playbook failed: connection timeout', 0),
('990e8400-e29b-41d4-a716-446655440016', '880e8400-e29b-41d4-a716-446655440005', 25, 'failed', '2024-02-12T12:32:05Z', '2024-02-12T12:35:05Z', 180, 'Ansible playbook failed: connection timeout', 1),
('990e8400-e29b-41d4-a716-446655440017', '880e8400-e29b-41d4-a716-446655440005', 25, 'failed', '2024-02-12T12:37:05Z', '2024-02-12T12:40:05Z', 180, 'Ansible playbook failed: connection timeout', 2),

-- Current running build
('990e8400-e29b-41d4-a716-446655440018', '880e8400-e29b-41d4-a716-446655440003', 0, 'started', '2024-02-12T10:30:00Z', '2024-02-12T10:30:05Z', 5, NULL, 0),
('990e8400-e29b-41d4-a716-446655440019', '880e8400-e29b-41d4-a716-446655440003', 5, 'completed', '2024-02-12T10:30:05Z', '2024-02-12T10:45:05Z', 900, NULL, 0),
('990e8400-e29b-41d4-a716-446655440020', '880e8400-e29b-41d4-a716-446655440003', 10, 'completed', '2024-02-12T10:45:05Z', '2024-02-12T10:55:05Z', 600, NULL, 0),
('990e8400-e29b-41d4-a716-446655440021', '880e8400-e29b-41d4-a716-446655440003', 15, 'completed', '2024-02-12T10:55:05Z', '2024-02-12T11:05:05Z', 600, NULL, 0),
('990e8400-e29b-41d4-a716-446655440022', '880e8400-e29b-41d4-a716-446655440003', 20, 'completed', '2024-02-12T11:05:05Z', '2024-02-12T11:15:05Z', 600, NULL, 0),
('990e8400-e29b-41d4-a716-446655440023', '880e8400-e29b-41d4-a716-446655440003', 25, 'completed', '2024-02-12T11:15:05Z', '2024-02-12T11:25:05Z', 600, NULL, 0),
('990e8400-e29b-41d4-a716-446655440024', '880e8400-e29b-41d4-a716-446655440003', 30, 'completed', '2024-02-12T11:25:05Z', '2024-02-12T11:35:05Z', 600, NULL, 0),
('990e8400-e29b-41d4-a716-446655440025', '880e8400-e29b-41d4-a716-446655440003', 35, 'completed', '2024-02-12T11:35:05Z', '2024-02-12T11:45:05Z', 600, NULL, 0),
('990e8400-e29b-41d4-a716-446655440026', '880e8400-e29b-41d4-a716-446655440003', 40, 'completed', '2024-02-12T11:45:05Z', '2024-02-12T11:55:05Z', 600, NULL, 0),
('990e8400-e29b-41d4-a716-446655440027', '880e8400-e29b-41d4-a716-446655440003', 45, 'started', '2024-02-12T11:55:05Z', NULL, NULL, NULL, 0);

-- Insert Build Failures
INSERT INTO build_failures (id, build_id, state, failure_type, error_message, error_details, component, retry_attempt, resolved, resolution_notes) VALUES
('aa0e8400-e29b-41d4-a716-446655440001', '880e8400-e29b-41d4-a716-446655440005', 25, 'ansible_error', 'Ansible playbook failed: connection timeout to target host', '{"playbook": "25-security.yml", "task": "Configure firewall", "host": "packer-build-vm", "error": "SSH connection failed after 30 retries"}', 'ansible', 1, FALSE, NULL),
('aa0e8400-e29b-41d4-a716-446655440002', '880e8400-e29b-41d4-a716-446655440005', 25, 'ansible_error', 'Ansible playbook failed: connection timeout to target host', '{"playbook": "25-security.yml", "task": "Configure firewall", "host": "packer-build-vm", "error": "SSH connection failed after 30 retries"}', 'ansible', 2, FALSE, NULL),
('aa0e8400-e29b-41d4-a716-446655440003', '880e8400-e29b-41d4-a716-446655440005', 25, 'ansible_error', 'Ansible playbook failed: connection timeout to target host', '{"playbook": "25-security.yml", "task": "Configure firewall", "host": "packer-build-vm", "error": "SSH connection failed after 30 retries"}', 'ansible', 3, FALSE, NULL),
('aa0e8400-e29b-41d4-a716-446655440004', '880e8400-e29b-41d4-a716-446655440006', 10, 'packer_error', 'Packer build failed: ISO download timeout', '{"builder": "amazon-ebs", "error": "Failed to download RHEL 8.10 ISO after 10 minutes", "url": "https://example.com/rhel-8.10.iso"}', 'packer', 1, FALSE, NULL);