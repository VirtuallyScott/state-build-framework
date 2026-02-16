# Resumable Builds - Quick Start Guide

> **💡 Note:** Examples below use curl for demonstration. For production pipelines, use the [`bldst` CLI tool](../buildstate_cli/README.md) for cleaner, more maintainable code.

## 🎉 What's Implemented

The resumable builds system is now live! Here's what you can do:

### ✅ Completed Features

1. **Database Schema** - 5 new tables created:
   - `build_artifacts` - Tracks snapshots, images, and other build outputs
   - `build_variables` - Stores VM IDs, network config, and other context
   - `resumable_states` - Defines which states can be resumed
   - `resume_requests` - Tracks resume operations
   - `build_jobs` - Links to CI/CD job information

2. **API Endpoints** - 15+ new endpoints:
   - Artifact management (`/builds/{id}/artifacts`)
   - Variable management (`/builds/{id}/variables`)
   - Resume context (`/builds/{id}/resume-context`)
   - Resume requests (`/builds/{id}/resume`)
   - Resumable state configuration (`/projects/{id}/resumable-states`)
   - Build job tracking (`/builds/{id}/jobs`)

3. **API Service** - Running and accessible at http://localhost:8080

## 🚀 Quick Test

### 1. View API Documentation

Open your browser to see the new endpoints:
- **Swagger UI**: http://localhost:8080/docs
  - Look for the "Artifacts", "Variables", and "Resume" sections

### 2. Test Artifact Registration

```bash
# Register an artifact (replace BUILD_ID with actual build ID)
curl -X POST http://localhost:8080/builds/BUILD_ID/artifacts \
  -H "X-API-Key: dev-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "state_code": 20,
    "artifact_name": "rhel9-snapshot-001",
    "artifact_type": "vm_snapshot",
    "artifact_path": "s3://my-bucket/snapshots/snapshot-001.vmdk",
    "storage_backend": "s3",
    "storage_region": "us-east-1",
    "storage_bucket": "my-bucket",
    "storage_key": "snapshots/snapshot-001.vmdk",
    "is_resumable": true,
    "metadata": {
      "vm_id": "i-abc123",
      "snapshot_id": "snap-xyz789"
    }
  }'
```

### 3. Set Build Variables

```bash
# Set a build variable
curl -X POST http://localhost:8080/builds/BUILD_ID/variables \
  -H "X-API-Key: dev-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "variable_key": "vm_instance_id",
    "variable_value": "i-0123456789abcdef",
    "set_at_state": 20,
    "is_required_for_resume": true
  }'
```

### 4. Get Resume Context

```bash
# Get everything needed to resume a build
curl -X GET http://localhost:8080/builds/BUILD_ID/resume-context \
  -H "X-API-Key: dev-key-12345"
```

Example response:
```json
{
  "build_id": "build-uuid-456",
  "current_state": 30,
  "last_successful_state": 30,
  "failed_state": 35,
  "resume_from_state": 35,
  "artifacts": [
    {
      "id": "art-123",
      "artifact_name": "rhel9-snapshot-001",
      "artifact_type": "vm_snapshot",
      "state_code": 20,
      "artifact_path": "s3://...",
      "is_resumable": true,
      "metadata": {"vm_id": "i-abc123"}
    }
  ],
  "variables": {
    "vm_instance_id": "i-0123456789abcdef",
    "vpc_id": "vpc-123456"
  },
  "resumable_state_config": null
}
```

### 5. Request Build Resume

```bash
# Request to resume a build
curl -X POST http://localhost:8080/builds/BUILD_ID/resume \
  -H "X-API-Key: dev-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "resume_from_state": 35,
    "resume_reason": "Network timeout during package installation",
    "requested_by": "ops-team"
  }'
```

## 📋 API Endpoint Reference

### Artifacts

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/builds/{build_id}/artifacts` | Register a new artifact |
| GET | `/builds/{build_id}/artifacts` | List all artifacts (with filters) |
| GET | `/builds/{build_id}/artifacts/{artifact_id}` | Get specific artifact |
| PATCH | `/builds/{build_id}/artifacts/{artifact_id}` | Update artifact metadata |
| DELETE | `/builds/{build_id}/artifacts/{artifact_id}` | Soft delete artifact (admin) |

### Variables

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/builds/{build_id}/variables` | Set a variable |
| GET | `/builds/{build_id}/variables` | List all variables |
| GET | `/builds/{build_id}/variables/dict` | Get as key-value dictionary |
| GET | `/builds/{build_id}/variables/{variable_key}` | Get specific variable |
| PATCH | `/builds/{build_id}/variables/{variable_key}` | Update variable |
| DELETE | `/builds/{build_id}/variables/{variable_key}` | Delete variable |

### Resume Operations

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/builds/{build_id}/resume-context` | Get complete resume context |
| POST | `/builds/{build_id}/resume` | Request build resume |
| GET | `/builds/{build_id}/resume-requests` | List resume requests |
| GET | `/resume-requests/{request_id}` | Get resume request details |
| PATCH | `/resume-requests/{request_id}` | Update resume request status |

### Resumable State Configuration

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/projects/{project_id}/resumable-states` | Define resumable state |
| GET | `/projects/{project_id}/resumable-states` | List resumable states |
| GET | `/projects/{project_id}/resumable-states/{state_code}` | Get specific config |
| PUT | `/projects/{project_id}/resumable-states/{state_code}` | Update config |

### Build Jobs

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/builds/{build_id}/jobs` | Link CI/CD job to build |
| GET | `/builds/{build_id}/jobs` | List all jobs for build |
| PATCH | `/builds/{build_id}/jobs/{job_id}` | Update job status |

## 🔐 Authentication

All endpoints require authentication via one of:
- **API Key**: `X-API-Key: dev-key-12345` (header)
- **JWT Token**: `Authorization: Bearer <token>` (header)

**Permission Levels:**
- **Read**: View artifacts, variables, resume context
- **Write**: Create/update artifacts, variables, resume requests
- **Admin**: Delete artifacts, manage system config

**Test Credentials** (see [CREDENTIALS.md](../CREDENTIALS.md)):
- `dev-key-12345` - read + write scopes
- `admin-key-99999` - all scopes

## 📝 Workflow Integration

### In Your Build Script

```bash
#!/bin/bash
BUILD_ID="your-build-id"
API_KEY="dev-key-12345"
API_URL="http://localhost:8080"

# State 20: Install packages (long-running)
echo "Installing packages..."
if ansible-playbook install-packages.yml; then
  # Success - create snapshot
  SNAPSHOT_ID=$(aws ec2 create-snapshot ...)
  
  # Register artifact
  curl -X POST "$API_URL/builds/$BUILD_ID/artifacts" \
    -H "X-API-Key: $API_KEY" \
    -H "Content-Type: application/json" \
    -d "{
      \"state_code\": 20,
      \"artifact_name\": \"packages-snapshot\",
      \"artifact_type\": \"ebs_snapshot\",
      \"artifact_path\": \"aws://snapshot/$SNAPSHOT_ID\",
      \"storage_backend\": \"aws\",
      \"is_resumable\": true,
      \"metadata\": {\"snapshot_id\": \"$SNAPSHOT_ID\"}
    }"
else
  # Failed - log error
  echo "Package installation failed"
  exit 1
fi
```

### In Your Resume Script

```bash
#!/bin/bash
BUILD_ID="$1"
API_KEY="dev-key-12345"
API_URL="http://localhost:8080"

# Get resume context
CONTEXT=$(curl -s -X GET "$API_URL/builds/$BUILD_ID/resume-context" \
  -H "X-API-Key: $API_KEY")

# Extract last snapshot
SNAPSHOT_ID=$(echo "$CONTEXT" | jq -r '.artifacts[] | select(.artifact_type == "ebs_snapshot") | .metadata.snapshot_id' | tail -1)

# Restore from snapshot
echo "Restoring from snapshot: $SNAPSHOT_ID"
aws ec2 create-volume --snapshot-id "$SNAPSHOT_ID" ...

# Continue build from last failed state
RESUME_FROM=$(echo "$CONTEXT" | jq -r '.resume_from_state')
echo "Resuming from state: $RESUME_FROM"
```

## 🎯 Next Steps

### Immediate (You can do this now!)
1. ✅ Test the endpoints via Swagger UI (http://localhost:8080/docs)
2. ✅ Integrate artifact registration into your build scripts
3. ✅ Set up variable tracking for VM IDs and other context

### Phase 2 (Future)
1. ⏳ CLI support (`bldst artifact register`, `bldst build resume`, etc.)
2. ⏳ Orchestrator service for automated resume triggers
3. ⏳ Webhook integration with Concourse/Jenkins
4. ⏳ Cleanup jobs for expired artifacts
5. ⏳ Metrics and dashboards for resume success rates

## 📚 Documentation

- **Design Document**: [docs/RESUMABLE_BUILDS_DESIGN.md](RESUMABLE_BUILDS_DESIGN.md)
- **API Reference**: http://localhost:8080/docs
- **Main Documentation**: [docs/INDEX.md](../docs/INDEX.md)
- **Credentials**: [CREDENTIALS.md](../CREDENTIALS.md)

## 🐛 Troubleshooting

### Check API Status
```bash
curl http://localhost:8080/health
```

### View API Logs
```bash
cd api_service/docker
docker compose logs api01 --tail=50
```

### Verify Database Tables
```bash
docker compose exec postgres psql -U buildapi -d builds -c "\dt build_*"
```

### Check Endpoints
```bash
curl -s http://localhost:8080/openapi.json | jq '.paths | keys[]' | grep artifact
```

## ✨ Summary

**You now have a fully functional resumable build system!** 

The foundation is in place for:
- Tracking artifacts at each build step
- Storing variables needed for resumption  
- Requesting and managing build resumes
- Configuring which states are resumable
- Linking builds to CI/CD jobs

Start integrating the artifact registration and variable tracking into your build scripts, and you'll be able to resume long-running builds from any point instead of starting over from scratch!

---

**Questions?** Review the [full design document](RESUMABLE_BUILDS_DESIGN.md) or test the endpoints at http://localhost:8080/docs
