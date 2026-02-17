-- Projects and State Codes Schema Extension for PostgreSQL
-- This extends the existing Build State database schema to support project-specific state definitions

-- Projects table (allows different teams/projects to define their own state workflows)
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,  -- UUID
    name TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- State Codes table (defines available states for each project)
CREATE TABLE IF NOT EXISTS state_codes (
    id TEXT PRIMARY KEY,  -- UUID
    project_id TEXT NOT NULL,
    name TEXT NOT NULL,  -- Human-readable name (e.g., 'completed', 'failed', 'building')
    display_name TEXT NOT NULL,
    description TEXT,
    color TEXT,  -- Optional hex color for UI (e.g., '#00FF00')
    is_initial BOOLEAN DEFAULT FALSE,  -- Whether this is the initial state for new builds
    is_final BOOLEAN DEFAULT FALSE,  -- Whether this is a final state
    is_error BOOLEAN DEFAULT FALSE,  -- Whether this represents an error state
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    UNIQUE(project_id, name)
);

-- Update builds table to reference projects and state codes
ALTER TABLE builds ADD COLUMN IF NOT EXISTS project_id TEXT;
ALTER TABLE builds ADD COLUMN IF NOT EXISTS current_state_code_id TEXT;
ALTER TABLE builds ADD FOREIGN KEY (project_id) REFERENCES projects(id);
ALTER TABLE builds ADD FOREIGN KEY (current_state_code_id) REFERENCES state_codes(id);

-- Update build_states table to reference state_codes
ALTER TABLE build_states ADD COLUMN IF NOT EXISTS state_code_id TEXT;
ALTER TABLE build_states ADD FOREIGN KEY (state_code_id) REFERENCES state_codes(id);

-- Indexes for the new tables
CREATE INDEX IF NOT EXISTS idx_state_codes_project_id ON state_codes(project_id);
CREATE INDEX IF NOT EXISTS idx_builds_project_id ON builds(project_id);
CREATE INDEX IF NOT EXISTS idx_build_states_state_code_id ON build_states(state_code_id);

-- Default project for existing builds
INSERT INTO projects (id, name, display_name, description) VALUES
('default-project-uuid', 'default', 'Default Project', 'Default project for existing builds')
ON CONFLICT (id) DO NOTHING;

-- Default state codes for the default project
INSERT INTO state_codes (id, project_id, name, display_name, description, color, is_initial, is_final, is_error) VALUES
('state-pending-uuid', 'default-project-uuid', 'pending', 'Pending', 'Build is pending', '#FFA500', true, false, false),
('state-building-uuid', 'default-project-uuid', 'building', 'Building', 'Build is in progress', '#0000FF', false, false, false),
('state-completed-uuid', 'default-project-uuid', 'completed', 'Completed', 'Build completed successfully', '#00FF00', false, true, false),
('state-failed-uuid', 'default-project-uuid', 'failed', 'Failed', 'Build failed', '#FF0000', false, true, true),
('state-cancelled-uuid', 'default-project-uuid', 'cancelled', 'Cancelled', 'Build was cancelled', '#808080', false, true, false)
ON CONFLICT (id) DO NOTHING;

-- Migrate existing builds to use the default project and appropriate state codes
UPDATE builds SET project_id = 'default-project-uuid' WHERE project_id IS NULL;

-- Migrate existing build_states to use state codes based on the old state numbers
UPDATE build_states SET state_code_id =
    CASE
        WHEN state = 0 THEN 'state-pending-uuid'
        WHEN state BETWEEN 1 AND 49 THEN 'state-building-uuid'
        WHEN state = 100 THEN 'state-completed-uuid'
        WHEN state BETWEEN 50 AND 99 THEN 'state-failed-uuid'
        ELSE 'state-failed-uuid'
    END
WHERE state_code_id IS NULL;

-- Update builds current_state_code_id based on the latest build_states entry
UPDATE builds SET current_state_code_id = (
    SELECT bs.state_code_id
    FROM build_states bs
    WHERE bs.build_id = builds.id
    ORDER BY bs.created_at DESC
    LIMIT 1
) WHERE current_state_code_id IS NULL;
('default-project-uuid', 'default', 'Default Project', 'Default project for existing builds');

-- Default state codes for the default project (matching current hardcoded states)
INSERT INTO state_codes (id, project_id, code, name, display_name, description, is_terminal, sort_order) VALUES
('state-pending-uuid', 'default-project-uuid', 0, 'pending', 'Pending', 'Build is queued and waiting to start', FALSE, 1),
('state-started-uuid', 'default-project-uuid', 1, 'started', 'Started', 'Build has started execution', FALSE, 2),
('state-building-uuid', 'default-project-uuid', 2, 'building', 'Building', 'Build is actively building the image', FALSE, 3),
('state-testing-uuid', 'default-project-uuid', 3, 'testing', 'Testing', 'Build is running tests', FALSE, 4),
('state-completed-uuid', 'default-project-uuid', 4, 'completed', 'Completed', 'Build completed successfully', TRUE, 5),
('state-failed-uuid', 'default-project-uuid', 5, 'failed', 'Failed', 'Build failed', TRUE, 6);

-- Update existing builds to use the default project
UPDATE builds SET project_id = 'default-project-uuid' WHERE project_id IS NULL;

-- Update existing build_states to reference the appropriate state_codes
UPDATE build_states SET state_code_id =
    CASE
        WHEN state = 0 THEN 'state-pending-uuid'
        WHEN state = 1 THEN 'state-started-uuid'
        WHEN state = 2 THEN 'state-building-uuid'
        WHEN state = 3 THEN 'state-testing-uuid'
        WHEN state = 4 THEN 'state-completed-uuid'
        WHEN state = 5 THEN 'state-failed-uuid'
        ELSE 'state-pending-uuid'  -- fallback
    END;

-- Make the new columns NOT NULL after migration
-- Note: In production, this would be done in separate migration steps
-- ALTER TABLE build_states ALTER COLUMN state_code_id SET NOT NULL;
-- ALTER TABLE builds ALTER COLUMN project_id SET NOT NULL;</content>
<parameter name="filePath">/Users/scottsmith/tmp/state-builds/api_service/schema_extension.sql