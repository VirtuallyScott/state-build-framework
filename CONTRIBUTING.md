# Contributing to Build State Tracking Framework

Thank you for your interest in contributing! This document outlines the standards, practices, and workflows for contributing to this project.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Naming Conventions](#naming-conventions)
- [Code Standards](#code-standards)
- [Database Changes](#database-changes)
- [Documentation](#documentation)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)

## Getting Started

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Git
- PostgreSQL knowledge (for database changes)

### Local Development Setup

```bash
# Clone the repository
git clone <repository-url>
cd state-builds

# Set up API service
cd api_service/docker
docker compose up -d

# Install CLI for testing
cd ../../bldst_cli
pip install -e .

# Configure CLI
bldst config set-url http://localhost:8080
bldst auth set-key dev-key-12345
```

## Development Workflow

We use **Git Flow** for branch management:

### Branch Structure

- `main` - Production-ready code
- `develop` - Integration branch for features
- `feature/*` - New features and enhancements
- `bugfix/*` - Bug fixes
- `hotfix/*` - Emergency production fixes
- `release/*` - Release preparation

### Creating a Feature Branch

```bash
# Start from develop
git checkout develop
git pull origin develop

# Create feature branch
git checkout -b feature/your-feature-name

# Work on your changes
git add .
git commit -m "feat: description of changes"

# Push to remote
git push origin feature/your-feature-name
```

### Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks
- `perf:` - Performance improvements
- `ci:` - CI/CD changes

**Examples:**

```
feat: add artifact storage tracking to build states

fix: correct authentication header validation

docs: update API reference with new endpoints

refactor: consolidate database connection logic
```

## Naming Conventions

### File Naming

- **Documentation files**: Use hyphens (`-`) for word separation
  - ✅ `API-REFERENCE.md`
  - ✅ `CI-CD-PIPELINE.md`
  - ❌ `API_REFERENCE.md`

- **Python files**: Use underscores (`_`) for word separation
  - ✅ `main_old.py`
  - ✅ `state_codes.py`

- **Shell scripts**: Use hyphens (`-`) for word separation, modern shebang
  - ✅ `test-api.sh` with `#!/usr/bin/env bash`
  - ✅ `version.sh` with `#!/usr/bin/env bash`
  - ❌ `#!/bin/bash` (not portable)
  - 📁 All scripts should be in `scripts/` directory

### Directory Naming

- **Directories**: Use underscores (`_`) for word separation
  - ✅ `api_service/`
  - ✅ `bldst_cli/`
  - ✅ `build_states/`

### Database Naming

- **Tables**: Use underscores, plural nouns
  - ✅ `build_states`
  - ✅ `os_versions`

- **Columns**: Use underscores, descriptive names
  - ✅ `artifact_storage_type`
  - ✅ `created_at`

## Code Standards

### Python Style

- Follow [PEP 8](https://pep8.org/)
- Use type hints where possible
- Maximum line length: 120 characters
- Use meaningful variable names

**Example:**

```python
from typing import Optional
from datetime import datetime

def create_build_state(
    build_id: str,
    state_code: int,
    status: str,
    artifact_path: Optional[str] = None
) -> dict:
    """
    Create a new build state record.
    
    Args:
        build_id: Unique identifier for the build
        state_code: State code (0-100 in increments of 5)
        status: Build status (pending, in_progress, completed, failed)
        artifact_path: Optional path to build artifact
        
    Returns:
        Dictionary containing the created state record
    """
    # Implementation
    pass
```

### FastAPI Endpoints

- Use descriptive endpoint names
- Include proper response models
- Add OpenAPI documentation
- Handle errors gracefully

**Example:**

```python
@router.post("/builds/{build_id}/state", response_model=BuildStateResponse)
async def add_build_state(
    build_id: str,
    state: StateTransition,
    db: Session = Depends(get_db)
):
    """
    Add a new state to a build's state progression.
    
    Tracks build progress through state codes 0-100.
    """
    # Implementation
    pass
```

### CLI Commands

- Use clear, action-oriented command names
- Provide helpful descriptions
- Include examples in help text
- Validate inputs early

**Example:**

```python
@app.command()
def add_state(
    build_id: str = typer.Argument(..., help="Build ID"),
    state_code: int = typer.Option(..., "--state-code", help="State code (0-100)"),
    storage_type: Optional[str] = typer.Option(None, "--storage-type", help="Storage type (s3, nfs, etc)")
):
    """
    Add a state to a build.
    
    Example:
        bldst build add-state BUILD123 --state-code 100 --storage-type s3
    """
    # Implementation
    pass
```

## Database Changes

### Schema Modifications

All database schema changes **must** include a migration script.

1. **Update the schema** in `api_service/init-db.sql`
2. **Create a migration script** in `api_service/` with descriptive name
   - Example: `artifact_storage_migration.sql`
3. **Include rollback instructions** in comments
4. **Document the changes** in commit message

**Migration Script Template:**

```sql
-- Migration: Add artifact storage tracking
-- Created: 2026-02-16
-- Description: Adds columns for tracking build artifact storage locations

BEGIN;

-- Add new columns
ALTER TABLE build_states 
ADD COLUMN artifact_storage_type VARCHAR(50),
ADD COLUMN artifact_storage_path TEXT,
ADD COLUMN artifact_size_bytes BIGINT,
ADD COLUMN artifact_checksum VARCHAR(64),
ADD COLUMN artifact_metadata JSONB;

-- Add indexes
CREATE INDEX idx_build_states_artifact_type 
ON build_states(artifact_storage_type);

-- Add comments
COMMENT ON COLUMN build_states.artifact_storage_type 
IS 'Type of storage: s3, nfs, ebs, ceph, azure_blob, gcs, local';

COMMIT;

-- ROLLBACK INSTRUCTIONS:
-- BEGIN;
-- DROP INDEX IF EXISTS idx_build_states_artifact_type;
-- ALTER TABLE build_states 
--   DROP COLUMN artifact_storage_type,
--   DROP COLUMN artifact_storage_path,
--   DROP COLUMN artifact_size_bytes,
--   DROP COLUMN artifact_checksum,
--   DROP COLUMN artifact_metadata;
-- COMMIT;
```

### SQLAlchemy Models

- Keep models in sync with database schema
- Use descriptive column names
- Include proper relationships
- Add docstrings for complex models

## Documentation

### Requirements

- **All new features** require documentation
- **API changes** must update API-REFERENCE.md
- **CLI changes** must update bldst_cli/README.md
- **Architecture changes** must update relevant design docs

### Documentation Files

Location structure:

```
docs/
├── PROBLEM-STATEMENT.md      # Framework overview
├── ARTIFACT-STORAGE.md        # Feature-specific docs
├── API-REFERENCE.md           # API endpoints (in api_service/docs/)
├── DATABASE-ARCHITECTURE.md   # Database design
├── CI-CD-PIPELINE.md          # CI/CD workflows
└── INDEX.md                   # Documentation hub
```

### Documentation Standards

- Use clear, concise language
- Include code examples
- Provide real-world use cases
- Keep examples up-to-date
- Use proper markdown formatting

**Example Documentation:**

```markdown
## Artifact Storage Tracking

Build artifacts can be tracked across multiple storage backends.

### Supported Storage Types

- **S3** - AWS S3 and compatible object storage
- **NFS** - Network File System shares
- **Azure Blob** - Azure Blob Storage
- **GCS** - Google Cloud Storage

### Example Usage

```bash
# Add state with artifact storage info
bldst build add-state BUILD123 \
  --state-code 100 \
  --storage-type s3 \
  --storage-path s3://my-bucket/rhel-9.3-ami.raw \
  --artifact-size 5368709120 \
  --checksum abc123...
```
```

## Testing

### Test Requirements

- All new features must include tests
- Bug fixes should include regression tests
- Maintain or improve code coverage
- Tests must pass before merging

### Running Tests

```bash
# API tests
cd api_service
pytest tests/ --cov=app --cov-report=term-missing

# CLI tests
cd bldst_cli
pytest tests/

# Integration tests
cd api_service/tests
../../scripts/test-api.sh
```

### Writing Tests

```python
import pytest
from app.models import BuildState

def test_create_build_state():
    """Test creating a build state with artifact storage."""
    state = BuildState(
        build_id="test-123",
        state_code=100,
        status="completed",
        artifact_storage_type="s3",
        artifact_storage_path="s3://bucket/artifact.raw"
    )
    assert state.artifact_storage_type == "s3"
    assert state.state_code == 100
```

## Pull Request Process

### Before Submitting

- [ ] Code follows style guidelines
- [ ] All tests pass locally
- [ ] Documentation is updated
- [ ] Commit messages follow conventions
- [ ] No merge conflicts with target branch
- [ ] Database migrations included (if applicable)

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Changes Made
- List of specific changes
- With bullet points

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed

## Database Changes
- [ ] Migration script included
- [ ] Schema documentation updated
- [ ] Rollback tested

## Documentation
- [ ] API reference updated
- [ ] CLI documentation updated
- [ ] Examples added/updated

## Screenshots (if applicable)
Add screenshots for UI changes

## Related Issues
Fixes #123
Relates to #456
```

### Review Process

1. Create PR from feature branch to `develop`
2. Automated checks must pass (CI/CD)
3. At least one reviewer approval required
4. Address review feedback
5. Squash and merge when approved

### After Merge

- Delete feature branch (local and remote)
- Update local `develop` branch
- Close related issues

```bash
# After PR merge
git checkout develop
git pull origin develop
git branch -d feature/your-feature-name
git push origin --delete feature/your-feature-name
```

## Project-Specific Guidelines

### State Codes

State codes must be in increments of 5 (0, 5, 10, 15, ..., 100):

- **0-15**: Preparation
- **20-45**: Building
- **50-75**: Configuration
- **80-95**: Testing
- **100**: Completed

### Artifact Storage Types

Supported types: `s3`, `nfs`, `ebs`, `ceph`, `azure_blob`, `gcs`, `local`

### API Keys and Authentication

- Never commit credentials
- Use environment variables
- Test credentials are documented in CREDENTIALS.md
- Production credentials use secret management

### Soft Deletes

Resources are never hard-deleted:

```python
# Don't do this
db.delete(resource)

# Do this instead
resource.deactivated_at = datetime.now()
db.commit()
```

## Questions?

- Check existing documentation in `docs/`
- Review closed issues and PRs
- Ask in pull request comments
- Contact maintainers

## Resources

- [API Reference](api_service/docs/API-REFERENCE.md)
- [CLI Documentation](bldst_cli/README.md)
- [Problem Statement](docs/PROBLEM-STATEMENT.md)
- [Documentation Index](docs/INDEX.md)

---

**Thank you for contributing!** 🚀
