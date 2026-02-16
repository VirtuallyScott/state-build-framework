# Artifact Storage Tracking

## Overview

The Build State API now tracks artifact storage locations for each build state. This enables distributed build systems where multiple build servers can access shared artifacts stored on various storage backends (S3, NFS, EBS, Ceph, etc.).

When a build state completes and produces an artifact, the system records where that artifact is stored so that subsequent build states can retrieve it from any server in the build server pool.

## Use Case

In a distributed build environment:

1. **Build Server A** completes state 10 and produces an artifact (e.g., a base VM image)
2. **Build Server A** uploads the artifact to shared storage (e.g., S3)
3. **Build Server A** records the artifact location in the build state
4. **Build Server B** picks up state 20 for the same build
5. **Build Server B** queries the build state history to find the artifact from state 10
6. **Build Server B** downloads the artifact from the shared storage location
7. **Build Server B** uses the artifact as the base for state 20 work

## Database Schema

The `build_states` table includes the following artifact tracking fields:

| Column | Type | Description |
|--------|------|-------------|
| `artifact_storage_type` | VARCHAR(50) | Type of storage backend (s3, nfs, ebs, ceph, local, etc.) |
| `artifact_storage_path` | TEXT | Full path/URI to the stored artifact |
| `artifact_size_bytes` | BIGINT | Size of the artifact in bytes |
| `artifact_checksum` | VARCHAR(128) | SHA256 or MD5 checksum for verification |
| `artifact_metadata` | JSONB | Additional metadata about the artifact |

## Supported Storage Types

The `artifact_storage_type` field accepts any string value, but common values include:

- `s3` - Amazon S3 or S3-compatible object storage
- `nfs` - Network File System
- `ebs` - Amazon Elastic Block Store (multi-mounted volumes)
- `ceph` - Ceph distributed storage
- `azure-blob` - Azure Blob Storage
- `gcs` - Google Cloud Storage
- `local` - Local filesystem (for testing only)
- `smb` - Windows SMB/CIFS shares
- `glusterfs` - GlusterFS distributed filesystem

## Storage Path Examples

### S3
```
s3://my-build-artifacts/project-123/build-456/state-10/artifact.qcow2
s3://company-builds/builds/2026-02-16/abc123-def456-state25.tar.gz
```

### NFS
```
/mnt/nfs/build-artifacts/project-123/build-456/state-10/artifact.qcow2
nfs://nfs-server.example.com/exports/builds/abc123/state-10.img
```

### EBS (Multi-Attach)
```
/mnt/ebs-shared/build-artifacts/project-123/build-456/state-10/artifact.qcow2
```

### Ceph
```
rbd:pool/build-artifacts/project-123/build-456/state-10
ceph://cluster-name/pool-name/abc123-state10
```

### Azure Blob
```
https://myaccount.blob.core.windows.net/build-artifacts/project-123/build-456/state-10/artifact.vhd
```

### Google Cloud Storage
```
gs://my-build-bucket/artifacts/project-123/build-456/state-10/artifact.tar.gz
```

## API Usage

### Creating a Build State with Artifact Information

When transitioning to a new build state, include artifact storage information:

**Request:**
```bash
curl -X POST "http://localhost:8080/builds/{build_id}/state" \
  -H "X-API-Key: dev-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "state_name": "package-installation",
    "message": "Packages installed successfully",
    "artifact_storage_type": "s3",
    "artifact_storage_path": "s3://my-builds/project-123/build-456/state-25/base-image.qcow2",
    "artifact_size_bytes": 2147483648,
    "artifact_checksum": "sha256:abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
    "artifact_metadata": {
      "compression": "gzip",
      "format": "qcow2",
      "virtual_size_gb": 100,
      "upload_duration_seconds": 45
    }
  }'
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "build_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "state": 25,
  "status": "completed",
  "start_time": "2026-02-16T10:30:00Z",
  "end_time": "2026-02-16T10:45:00Z",
  "duration_seconds": 900,
  "artifact_storage_type": "s3",
  "artifact_storage_path": "s3://my-builds/project-123/build-456/state-25/base-image.qcow2",
  "artifact_size_bytes": 2147483648,
  "artifact_checksum": "sha256:abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
  "artifact_metadata": {
    "compression": "gzip",
    "format": "qcow2",
    "virtual_size_gb": 100,
    "upload_duration_seconds": 45
  },
  "created_at": "2026-02-16T10:30:00Z"
}
```

### Querying Build State History for Artifacts

Get all build states to find artifacts:

```bash
curl "http://localhost:8080/builds/{build_id}/states" \
  -H "X-API-Key: readonly-key-888"
```

Query the database directly to find the latest artifact for a specific state:

```sql
SELECT 
    artifact_storage_type,
    artifact_storage_path,
    artifact_size_bytes,
    artifact_checksum,
    artifact_metadata
FROM build_states
WHERE build_id = '7c9e6679-7425-40de-944b-e07fc1f90ae7' 
  AND state = 25
  AND artifact_storage_path IS NOT NULL
ORDER BY created_at DESC
LIMIT 1;
```

## CLI Usage

### Add a Build State with Artifact Information

```bash
bldst build add-state {build-id} \
  --state 25 \
  --status completed \
  --storage-type s3 \
  --storage-path "s3://my-builds/project-123/build-456/state-25/base-image.qcow2" \
  --artifact-size 2147483648 \
  --checksum "sha256:abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789"
```

### Parameters

| Parameter | Description | Required |
|-----------|-------------|----------|
| `--storage-type` | Type of storage backend (s3, nfs, ebs, ceph, etc.) | No |
| `--storage-path` | Full path/URI to the stored artifact | No |
| `--artifact-size` | Size of the artifact in bytes | No |
| `--checksum` | SHA256 or MD5 checksum for verification | No |

## Best Practices

### 1. Always Include Storage Type and Path Together

When uploading an artifact, always provide both `artifact_storage_type` and `artifact_storage_path`:

```json
{
  "artifact_storage_type": "s3",
  "artifact_storage_path": "s3://bucket/path/to/artifact"
}
```

### 2. Use Checksums for Verification

Always include checksums to verify artifact integrity:

```json
{
  "artifact_checksum": "sha256:abc123..."
}
```

### 3. Include Size for Optimization

Recording artifact size helps with:
- Storage planning
- Download estimation
- Resource allocation

```json
{
  "artifact_size_bytes": 2147483648
}
```

### 4. Use Metadata for Additional Context

Store helpful metadata about the artifact:

```json
{
  "artifact_metadata": {
    "format": "qcow2",
    "compression": "gzip",
    "virtual_size_gb": 100,
    "created_by": "packer",
    "packer_version": "1.9.0",
    "upload_duration_seconds": 45,
    "region": "us-east-1"
  }
}
```

### 5. Use URIs for Clarity

Use full URIs for storage paths to avoid ambiguity:

**Good:**
```
s3://my-bucket/builds/abc123/state-10.qcow2
nfs://server.example.com/exports/builds/abc123.img
```

**Not Recommended:**
```
/builds/abc123/state-10.qcow2  (ambiguous - local or NFS?)
abc123/state-10.qcow2          (missing protocol)
```

### 6. Consistent Naming Conventions

Establish a consistent naming pattern for artifacts:

```
{storage-type}://{location}/{project-id}/{build-id}/state-{state-code}/{filename}
```

Example:
```
s3://build-artifacts/project-a1b2c3/build-d4e5f6/state-25/base-image.qcow2
```

## Migration

### Applying the Migration

For existing databases, run the migration script:

```bash
psql -U buildstate -d buildstate -f api_service/artifact_storage_migration.sql
```

### Migration Script

The migration adds the following columns to `build_states`:

```sql
ALTER TABLE build_states 
ADD COLUMN IF NOT EXISTS artifact_storage_type VARCHAR(50),
ADD COLUMN IF NOT EXISTS artifact_storage_path TEXT,
ADD COLUMN IF NOT EXISTS artifact_size_bytes BIGINT,
ADD COLUMN IF NOT EXISTS artifact_checksum VARCHAR(128),
ADD COLUMN IF NOT EXISTS artifact_metadata JSONB;

CREATE INDEX IF NOT EXISTS idx_build_states_artifact_storage_type 
ON build_states(artifact_storage_type);

CREATE INDEX IF NOT EXISTS idx_build_states_build_id_state 
ON build_states(build_id, state);
```

## Example Workflow

### Complete Build Workflow with Artifacts

```bash
#!/bin/bash
# Example: Distributed build workflow with artifact tracking

API_URL="http://localhost:8080"
API_KEY="dev-key-12345"
BUILD_ID="7c9e6679-7425-40de-944b-e07fc1f90ae7"
PROJECT_BUCKET="s3://my-build-artifacts"

# State 10: Create base VM image
echo "State 10: Creating base image..."
packer build base-image.pkr.hcl
BASE_IMAGE="base-image.qcow2"

# Upload to S3
echo "Uploading base image to S3..."
CHECKSUM=$(sha256sum "$BASE_IMAGE" | awk '{print $1}')
SIZE=$(stat -f%z "$BASE_IMAGE")
aws s3 cp "$BASE_IMAGE" "$PROJECT_BUCKET/$BUILD_ID/state-10/$BASE_IMAGE"

# Record artifact location
curl -X POST "$API_URL/builds/$BUILD_ID/state" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"state_name\": \"base-image-created\",
    \"message\": \"Base image created and uploaded\",
    \"artifact_storage_type\": \"s3\",
    \"artifact_storage_path\": \"$PROJECT_BUCKET/$BUILD_ID/state-10/$BASE_IMAGE\",
    \"artifact_size_bytes\": $SIZE,
    \"artifact_checksum\": \"sha256:$CHECKSUM\"
  }"

# State 20: Install packages (may run on different server)
echo "State 20: Installing packages..."

# Download previous artifact
PREV_ARTIFACT=$(curl -s "$API_URL/builds/$BUILD_ID/states" \
  -H "X-API-Key: $API_KEY" \
  | jq -r '.[] | select(.state == 10) | .artifact_storage_path')

echo "Downloading artifact from: $PREV_ARTIFACT"
aws s3 cp "$PREV_ARTIFACT" "base-image.qcow2"

# Verify checksum
EXPECTED_CHECKSUM=$(curl -s "$API_URL/builds/$BUILD_ID/states" \
  -H "X-API-Key: $API_KEY" \
  | jq -r '.[] | select(.state == 10) | .artifact_checksum' \
  | sed 's/sha256://')

ACTUAL_CHECKSUM=$(sha256sum base-image.qcow2 | awk '{print $1}')

if [ "$EXPECTED_CHECKSUM" != "$ACTUAL_CHECKSUM" ]; then
  echo "ERROR: Checksum mismatch!"
  exit 1
fi

echo "Checksum verified successfully!"

# Continue with package installation...
# ... build process continues ...
```

## Troubleshooting

### Artifact Not Found

If a build server cannot find an artifact:

1. Verify the build state was recorded correctly:
   ```bash
   curl "$API_URL/builds/{build_id}/states" -H "X-API-Key: $API_KEY" | jq
   ```

2. Check the artifact exists in storage:
   ```bash
   aws s3 ls s3://bucket/path/to/artifact
   ```

3. Verify access permissions to the storage backend

### Checksum Mismatch

If checksums don't match:

1. Re-download the artifact
2. Check for network corruption
3. Verify the upload was successful
4. Consider re-uploading the artifact

### Performance Issues

For large artifacts:

1. Use compression when possible
2. Consider multi-part uploads for large files
3. Use storage in the same region as build servers
4. Implement caching strategies for frequently accessed artifacts

## Security Considerations

1. **Access Control**: Ensure build servers have appropriate IAM roles or credentials for storage access
2. **Encryption**: Use encryption at rest and in transit (e.g., S3 SSE, TLS)
3. **Checksums**: Always verify checksums to detect corruption or tampering
4. **Lifecycle Policies**: Implement storage lifecycle policies to manage costs
5. **Audit Logging**: Enable audit logging on storage backends for compliance

## Future Enhancements

Potential future enhancements to artifact storage tracking:

- Automatic artifact cleanup/expiration
- Artifact retention policies
- Multi-region artifact replication
- Artifact caching layer
- Automatic checksum verification in API
- Artifact version tracking
- Artifact dependency graphs

---

**Last Updated**: February 16, 2026
