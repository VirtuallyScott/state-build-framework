-- Migration: Add artifact storage tracking to build_states table
-- Date: February 16, 2026
-- Description: Add columns to track where artifacts are stored after each build state
--              to enable distributed build servers to access artifacts from shared storage

-- Add new columns to build_states table
ALTER TABLE build_states 
ADD COLUMN IF NOT EXISTS artifact_storage_type VARCHAR(50),
ADD COLUMN IF NOT EXISTS artifact_storage_path TEXT,
ADD COLUMN IF NOT EXISTS artifact_size_bytes BIGINT,
ADD COLUMN IF NOT EXISTS artifact_checksum VARCHAR(128),
ADD COLUMN IF NOT EXISTS artifact_metadata JSONB;

-- Add comments for documentation
COMMENT ON COLUMN build_states.artifact_storage_type IS 'Type of storage where artifact is stored (s3, nfs, ebs, ceph, local, etc.)';
COMMENT ON COLUMN build_states.artifact_storage_path IS 'Full path/URI to the stored artifact (e.g., s3://bucket/path, /mnt/nfs/path, etc.)';
COMMENT ON COLUMN build_states.artifact_size_bytes IS 'Size of the artifact in bytes';
COMMENT ON COLUMN build_states.artifact_checksum IS 'SHA256 or MD5 checksum of the artifact for verification';
COMMENT ON COLUMN build_states.artifact_metadata IS 'Additional metadata about the artifact (JSON format)';

-- Create index on artifact_storage_type for faster queries
CREATE INDEX IF NOT EXISTS idx_build_states_artifact_storage_type 
ON build_states(artifact_storage_type);

-- Create index on build_id and state for finding artifacts by build and state
CREATE INDEX IF NOT EXISTS idx_build_states_build_id_state 
ON build_states(build_id, state);

-- Example query to find the latest artifact for a specific build state
-- SELECT artifact_storage_type, artifact_storage_path, artifact_size_bytes, artifact_checksum
-- FROM build_states
-- WHERE build_id = '<build_id>' AND state = <state_code> 
-- ORDER BY created_at DESC
-- LIMIT 1;
