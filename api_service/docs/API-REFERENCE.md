# Build State API Reference

Complete API Reference for the Build State Management System.

> **💡 Recommended for Pipelines:** Use the [`bldst` CLI tool](../../bldst_cli/README.md) for cleaner, more maintainable pipeline code. See [README.md](README.md) for CLI examples.
>
> This document is the **complete API reference** for direct HTTP access, testing, and understanding the underlying API structure.

## Base URL

```
http://localhost:8080
```

In production, replace with your deployed API URL.

## Authentication

All endpoints (except `/health`, `/ready`, and `/status`) require authentication. Two methods are supported:

### CLI Authentication (Recommended)
```bash
# One-time configuration
bldst config set-url http://localhost:8080
bldst auth set-key your-api-key

# Use commands
bldst platform list
bldst build create --build-number "my-build" ...
```

### API Key (Direct HTTP access)
```bash
curl -H "X-API-Key: your-api-key" http://localhost:8080/platforms/
```

### JWT Bearer Token (Direct HTTP access)
```bash
# Get token first
TOKEN=$(curl -X POST http://localhost:8080/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123" | jq -r '.access_token')

# Use token
curl -H "Authorization: Bearer $TOKEN" http://localhost:8080/platforms/
```

## Authorization Scopes

- **read** - View resources (GET operations)
- **write** - Create and update resources (POST, PUT operations) + read
- **admin** - Delete resources (DELETE operations) + write + read

## API Endpoints

### Health & Status

#### GET /health
Check API health status.

**Authentication:** None required

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-02-14T17:30:00Z"
}
```

#### GET /ready
Check if API is ready to accept requests.

**Authentication:** None required

**Response:**
```json
{
  "ready": true,
  "database": "connected",
  "timestamp": "2026-02-14T17:30:00Z"
}
```

#### GET /status
Detailed system status including version and uptime.

**Authentication:** None required

**Response:**
```json
{
  "version": "1.0.0",
  "uptime": 123456,
  "status": "running"
}
```

---

### Authentication

#### POST /token
Obtain JWT access token.

**Authentication:** None required (uses form data for credentials)

**Request:**
```bash
curl -X POST http://localhost:8080/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### POST /auth/idm
Alternative authentication endpoint for IDM integration.

**Authentication:** None required

**Request:**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Response:** Same as `/token`

---

### Platforms

Manage cloud platforms (AWS, Azure, GCP, etc.).

#### POST /platforms/
Create a new platform.

**Authorization:** `write` scope required

**Request:**
```json
{
  "name": "aws-us-east-1",
  "cloud_provider": "aws",
  "region": "us-east-1"
}
```

**Response (201):**
```json
{
  "id": "aws-us-east-1",
  "name": "aws-us-east-1",
  "cloud_provider": "aws",
  "region": "us-east-1",
  "created_at": "2026-02-14T17:30:00Z",
  "deactivated_at": null
}
```

#### GET /platforms/
List all active platforms.

**Authorization:** `read` scope required

**Query Parameters:**
- `skip` (int, default: 0) - Number of records to skip
- `limit` (int, default: 100) - Maximum records to return
- `include_deactivated` (bool, default: false) - Include soft-deleted platforms

**Response:**
```json
[
  {
    "id": "aws-commercial",
    "name": "AWS Commercial",
    "cloud_provider": "aws",
    "region": "us-east-1",
    "created_at": "2026-02-14T17:30:00Z",
    "deactivated_at": null
  }
]
```

#### GET /platforms/{platform_id}
Get a specific platform by ID.

**Authorization:** `read` scope required

**Response:**
```json
{
  "id": "aws-commercial",
  "name": "AWS Commercial",
  "cloud_provider": "aws",
  "region": "us-east-1",
  "created_at": "2026-02-14T17:30:00Z",
  "deactivated_at": null
}
```

#### PUT /platforms/{platform_id}
Update a platform.

**Authorization:** `write` scope required

**Request:**
```json
{
  "name": "AWS Commercial Updated",
  "region": "us-west-2"
}
```

**Response:** Updated platform object

#### DELETE /platforms/{platform_id}
Soft delete a platform.

**Authorization:** `admin` scope required

**Response:** 204 No Content

---

### OS Versions

Manage operating system versions.

#### POST /os_versions/
Create a new OS version.

**Authorization:** `write` scope required

**Request:**
```json
{
  "name": "Red Hat Enterprise Linux",
  "version": "9.3"
}
```

**Response (201):**
```json
{
  "id": "cd515391-01e8-4b34-9004-ad0a32c2fb25",
  "name": "Red Hat Enterprise Linux",
  "version": "9.3",
  "created_at": "2026-02-14T17:30:00Z",
  "deactivated_at": null
}
```

#### GET /os_versions/
List all active OS versions.

**Authorization:** `read` scope required

**Query Parameters:**
- `skip` (int, default: 0)
- `limit` (int, default: 100)
- `include_deactivated` (bool, default: false)

**Response:** Array of OS version objects

#### GET /os_versions/{os_version_id}
Get a specific OS version.

**Authorization:** `read` scope required

#### PUT /os_versions/{os_version_id}
Update an OS version.

**Authorization:** `write` scope required

**Request:**
```json
{
  "version": "9.4"
}
```

#### DELETE /os_versions/{os_version_id}
Soft delete an OS version.

**Authorization:** `admin` scope required

---

### Image Types

Manage image types (Base, HANA, SAP App, etc.).

#### POST /image_types/
Create a new image type.

**Authorization:** `write` scope required

**Request:**
```json
{
  "name": "kubernetes-node",
  "description": "Kubernetes worker node image"
}
```

**Response (201):**
```json
{
  "id": "ce74e171-83ce-4390-bb46-e8806908d818",
  "name": "kubernetes-node",
  "description": "Kubernetes worker node image",
  "created_at": "2026-02-14T17:30:00Z",
  "deactivated_at": null
}
```

#### GET /image_types/
List all active image types.

**Authorization:** `read` scope required

**Query Parameters:**
- `skip` (int, default: 0)
- `limit` (int, default: 100)
- `include_deactivated` (bool, default: false)

#### GET /image_types/{image_type_id}
Get a specific image type.

**Authorization:** `read` scope required

#### PUT /image_types/{image_type_id}
Update an image type.

**Authorization:** `write` scope required

#### DELETE /image_types/{image_type_id}
Soft delete an image type.

**Authorization:** `admin` scope required

---

### Projects

Manage build projects.

#### POST /projects/
Create a new project.

**Authorization:** `write` scope required

**Request:**
```json
{
  "name": "rhel-8-base",
  "description": "RHEL 8 base image builds"
}
```

**Response (201):**
```json
{
  "id": "12345",
  "name": "rhel-8-base",
  "description": "RHEL 8 base image builds",
  "created_at": "2026-02-14T17:30:00Z",
  "deactivated_at": null
}
```

#### GET /projects/
List all active projects.

**Authorization:** `read` scope required

#### GET /projects/{project_id}
Get a specific project.

**Authorization:** `read` scope required

#### PUT /projects/{project_id}
Update a project.

**Authorization:** `write` scope required

#### DELETE /projects/{project_id}
Soft delete a project.

**Authorization:** `admin` scope required

---

### State Codes

Manage state codes within projects.

#### POST /projects/{project_id}/state-codes
Create a state code definition for a project.

**Authorization:** `write` scope required

**Request:**
```json
{
  "state_code": 5,
  "description": "Preparing build environment",
  "is_blocking": false
}
```

**Response (201):**
```json
{
  "id": "abc-123",
  "project_id": "12345",
  "state_code": 5,
  "description": "Preparing build environment",
  "is_blocking": false,
  "created_at": "2026-02-14T17:30:00Z"
}
```

#### GET /projects/{project_id}/state-codes
List state codes for a project.

**Authorization:** `read` scope required

#### GET /projects/{project_id}/state-codes/{state_code_id}
Get a specific state code.

**Authorization:** `read` scope required

#### PUT /projects/{project_id}/state-codes/{state_code_id}
Update a state code.

**Authorization:** `write` scope required

#### DELETE /projects/{project_id}/state-codes/{state_code_id}
Delete a state code.

**Authorization:** `admin` scope required

---

### Builds

Manage build instances and their states.

#### POST /builds
Create a new build.

**Authorization:** `write` scope required

**Request:**
```json
{
  "project_id": "12345",
  "platform_id": "aws-commercial",
  "os_version_id": "rhel-9.3",
  "image_type_id": "base",
  "build_number": "2024.02.001",
  "build_metadata": {
    "initiated_by": "concourse-pipeline",
    "commit_sha": "abc123"
  }
}
```

**Response (201):**
```json
{
  "id": "build-uuid-123",
  "project_id": "12345",
  "platform_id": "aws-commercial",
  "os_version_id": "rhel-9.3",
  "image_type_id": "base",
  "build_number": "2024.02.001",
  "current_state": 0,
  "status": "pending",
  "created_at": "2026-02-14T17:30:00Z",
  "updated_at": "2026-02-14T17:30:00Z"
}
```

#### POST /builds/{build_id}/state
Update build state (progress tracking).

**Authorization:** `write` scope required

**Request:**
```json
{
  "state_code": 15,
  "status": "in_progress",
  "message": "Installing base packages",
  "metadata": {
    "progress_percent": 30
  },
  "artifact_storage_type": "s3",
  "artifact_storage_path": "s3://my-builds/project-123/build-456/state-15/base-image.qcow2",
  "artifact_size_bytes": 2147483648,
  "artifact_checksum": "sha256:abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
  "artifact_metadata": {
    "compression": "gzip",
    "format": "qcow2"
  }
}
```

**Request Fields:**
- `state_code` (int, required) - State code number
- `status` (string, required) - Status: pending, in_progress, completed, failed
- `message` (string, optional) - Human-readable status message
- `metadata` (object, optional) - Additional state metadata
- `artifact_storage_type` (string, optional) - Storage type: s3, nfs, ebs, ceph, local, etc.
- `artifact_storage_path` (string, optional) - Full path/URI to stored artifact
- `artifact_size_bytes` (int, optional) - Size of artifact in bytes
- `artifact_checksum` (string, optional) - SHA256 or MD5 checksum for verification
- `artifact_metadata` (object, optional) - Additional artifact metadata

**Response:**
```json
{
  "build_id": "build-uuid-123",
  "state_code": 15,
  "status": "in_progress",
  "message": "Installing base packages",
  "artifact_storage_type": "s3",
  "artifact_storage_path": "s3://my-builds/project-123/build-456/state-15/base-image.qcow2",
  "artifact_size_bytes": 2147483648,
  "artifact_checksum": "sha256:abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
  "artifact_metadata": {
    "compression": "gzip",
    "format": "qcow2"
  },
  "timestamp": "2026-02-14T17:30:00Z"
}
```

> 📖 For detailed information on artifact storage tracking, see [Artifact Storage Tracking](../../docs/ARTIFACT-STORAGE.md).

#### POST /builds/{build_id}/failure
Record build failure.

**Authorization:** `write` scope required

**Request:**
```json
{
  "state_code": 25,
  "error_message": "Package installation failed",
  "error_details": {
    "package": "httpd",
    "exit_code": 1
  },
  "is_retryable": true
}
```

#### GET /builds
List all builds.

**Authorization:** `read` scope required

**Query Parameters:**
- `skip` (int, default: 0)
- `limit` (int, default: 100)
- `project_id` (string, optional) - Filter by project
- `status` (string, optional) - Filter by status (pending, in_progress, completed, failed)

#### GET /builds/{build_id}
Get build details.

**Authorization:** `read` scope required

#### GET /builds/{build_id}/state
Get current state of a build.

**Authorization:** `read` scope required

**Response:**
```json
{
  "build_id": "build-uuid-123",
  "current_state": 45,
  "status": "in_progress",
  "last_updated": "2026-02-14T17:30:00Z",
  "history": [
    {
      "state_code": 0,
      "status": "pending",
      "timestamp": "2026-02-14T17:00:00Z"
    },
    {
      "state_code": 15,
      "status": "in_progress",
      "timestamp": "2026-02-14T17:15:00Z"
    }
  ]
}
```

---

### Dashboard

Aggregate views and statistics.

#### GET /dashboard/summary
Get dashboard summary with statistics.

**Authorization:** `read` scope required

**Response:**
```json
{
  "total_builds": 150,
  "active_builds": 12,
  "completed_builds": 130,
  "failed_builds": 8,
  "platforms": 5,
  "projects": 8
}
```

#### GET /dashboard/recent
Get recent builds.

**Authorization:** `read` scope required

**Query Parameters:**
- `limit` (int, default: 10)

#### GET /dashboard/platform/{platform_id}
Get statistics for a specific platform.

**Authorization:** `read` scope required

---

### Users

Manage user accounts and API tokens.

#### POST /users
Create a new user.

**Authorization:** `admin` scope required

**Request:**
```json
{
  "username": "newuser",
  "email": "user@example.com",
  "password": "secure-password",
  "scopes": ["read", "write"]
}
```

**Response (201):**
```json
{
  "id": "user-uuid-123",
  "username": "newuser",
  "email": "user@example.com",
  "scopes": ["read", "write"],
  "is_active": true,
  "created_at": "2026-02-14T17:30:00Z"
}
```

#### GET /users
List all users.

**Authorization:** `admin` scope required

#### GET /users/me
Get current authenticated user.

**Authorization:** Any valid authentication

#### GET /users/{user_id}
Get specific user.

**Authorization:** `admin` scope required

#### PUT /users/{user_id}
Update user.

**Authorization:** `admin` scope required

#### DELETE /users/{user_id}
Delete user.

**Authorization:** `admin` scope required

#### POST /users/{user_id}/tokens
Create API token for user.

**Authorization:** `admin` scope required

**Request:**
```json
{
  "name": "Pipeline Token",
  "scopes": ["read", "write"],
  "expires_in_days": 365
}
```

**Response:**
```json
{
  "token": "dev-key-12345",
  "name": "Pipeline Token",
  "scopes": ["read", "write"],
  "expires_at": "2027-02-14T17:30:00Z"
}
```

#### GET /users/{user_id}/tokens
List user's API tokens.

**Authorization:** `admin` scope required

#### DELETE /users/{user_id}/tokens/{token_id}
Revoke API token.

**Authorization:** `admin` scope required

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message description"
}
```

### HTTP Status Codes

- **200** - Success
- **201** - Created
- **204** - No Content (successful deletion)
- **400** - Bad Request (validation error)
- **401** - Unauthorized (authentication required)
- **403** - Forbidden (insufficient permissions)
- **404** - Not Found
- **409** - Conflict (duplicate resource)
- **422** - Unprocessable Entity (schema validation failed)
- **500** - Internal Server Error

### Common Error Scenarios

**Missing Authentication:**
```json
{
  "detail": "Authentication required. Use Bearer token or X-API-Key."
}
```

**Insufficient Permissions:**
```json
{
  "detail": "Admin permission required"
}
```

**Resource Not Found:**
```json
{
  "detail": "Platform with id 'unknown-platform' not found"
}
```

**Validation Error:**
```json
{
  "detail": [
    {
      "loc": ["body", "name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## Rate Limiting

Currently not implemented. For production deployments, consider implementing rate limiting at the nginx level.

---

## Pagination

List endpoints support pagination via `skip` and `limit` query parameters:

```bash
# Get second page of 50 results
curl http://localhost:8080/platforms/?skip=50&limit=50
```

---

## Filtering

Some endpoints support filtering via query parameters. See individual endpoint documentation for available filters.

---

## Interactive API Documentation

FastAPI provides automatic interactive API documentation:

- **Swagger UI**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc

These interfaces allow you to:
- Browse all endpoints
- View request/response schemas
- Test API calls directly in the browser
- Download OpenAPI specification

---

## Example Workflows

### Complete Build Workflow

```bash
# 1. Authenticate
export API_KEY="dev-key-12345"
export API_URL="http://localhost:8080"

# 2. Create project
PROJECT_ID=$(curl -s -X POST "$API_URL/projects/" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name": "rhel-9-base", "description": "RHEL 9 base images"}' \
  | jq -r '.id')

# 3. Create build
BUILD_ID=$(curl -s -X POST "$API_URL/builds" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"project_id\": \"$PROJECT_ID\",
    \"platform_id\": \"aws-commercial\",
    \"os_version_id\": \"rhel-9.3\",
    \"image_type_id\": \"base\",
    \"build_number\": \"2024.02.001\"
  }" | jq -r '.id')

# 4. Update state as build progresses
curl -X POST "$API_URL/builds/$BUILD_ID/state" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"state_code": 5, "status": "in_progress", "message": "Starting build"}'

curl -X POST "$API_URL/builds/$BUILD_ID/state" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"state_code": 25, "status": "in_progress", "message": "Installing packages"}'

# 5. Check build status
curl -s "$API_URL/builds/$BUILD_ID/state" \
  -H "X-API-Key: $API_KEY" | jq
```

### Query and Filter

```bash
# List builds for specific project
curl -s "$API_URL/builds?project_id=$PROJECT_ID" \
  -H "X-API-Key: $API_KEY" | jq

# List only failed builds
curl -s "$API_URL/builds?status=failed" \
  -H "X-API-Key: $API_KEY" | jq

# Get dashboard summary
curl -s "$API_URL/dashboard/summary" \
  -H "X-API-Key: $API_KEY" | jq
```

---

## Additional Resources

- [Authentication Guide](AUTHENTICATION.md)
- [Deployment Guide](README.md#deployment)
- [Architecture Overview](ARCHITECTURE.md)
- [CLI Documentation](../../bldst_cli/README.md)
