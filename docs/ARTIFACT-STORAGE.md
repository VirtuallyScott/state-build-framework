# Artifact Storage Tracking

## Overview

The Build State API provides comprehensive artifact storage tracking to enable resumable builds and distributed build systems. Artifacts are tracked in two complementary ways:

1. **Build States Table** - Quick artifact reference for each build state transition
2. **Build Artifacts Table** - Comprehensive artifact registry with full metadata and lifecycle management

This dual approach allows for:
- Quick lookups during state transitions (via `build_states`)
- Full artifact lifecycle management for resumable builds (via `build_artifacts`)
- Distributed build systems where multiple servers share artifacts via cloud storage
- Integrity verification using SHA256 checksums

## Use Cases

### 1. Distributed Build Systems

In a distributed build environment:

1. **Build Server A** completes state 10 and produces an artifact (e.g., a base VM image)
2. **Build Server A** uploads the artifact to shared storage (e.g., S3)
3. **Build Server A** records the artifact location in the database
4. **Build Server B** picks up state 20 for the same build
5. **Build Server B** queries the artifact registry to find the artifact from state 10
6. **Build Server B** downloads the artifact from the shared storage location
7. **Build Server B** verifies integrity using SHA256 checksum
8. **Build Server B** uses the artifact as the base for state 20 work

### 2. Resumable Builds

When a build fails:

1. Query `build_artifacts` for resumable artifacts (`is_resumable = TRUE`)
2. Find the last successful state with a resumable artifact
3. Restore VM/environment from the stored artifact
4. Resume build from the next state
5. Save hours of rebuild time

## Database Schema

### Build States Table (Quick Reference)

The `build_states` table includes artifact tracking fields for quick lookups:

| Column | Type | Description |
|--------|------|-------------|
| `artifact_storage_type` | VARCHAR(50) | Type of storage backend (s3, nfs, ebs, ceph, local, etc.) |
| `artifact_storage_path` | TEXT | Full path/URI to the stored artifact |
| `artifact_size_bytes` | BIGINT | Size of the artifact in bytes |
| `artifact_checksum` | VARCHAR(128) | SHA256 or MD5 checksum for verification |
| `artifact_metadata` | JSONB | Additional metadata about the artifact |

### Build Artifacts Table (Full Registry)

The `build_artifacts` table provides comprehensive artifact management:

| Column | Type | Description |
|--------|------|-------------|
| `id` | TEXT (UUID) | Unique artifact identifier |
| `build_id` | TEXT (UUID) | Build this artifact belongs to |
| `state_code` | INTEGER | State at which this artifact was created |
| `artifact_name` | TEXT | Unique name within the build |
| `artifact_type` | TEXT | Type: vm_snapshot, ami, disk_image, config_file, etc. |
| `artifact_path` | TEXT | Full path/URL to the artifact |
| `storage_backend` | TEXT | Backend: s3, azure_blob, gcp_storage, local, vsphere, nfs, etc. |
| `storage_region` | TEXT | Storage region (if applicable) |
| `storage_bucket` | TEXT | Bucket or container name |
| `storage_key` | TEXT | Key/path within bucket |
| `size_bytes` | BIGINT | Size of artifact in bytes |
| `checksum` | TEXT | SHA256 checksum for integrity verification |
| `checksum_algorithm` | TEXT | Algorithm used (default: sha256) |
| `is_resumable` | BOOLEAN | Can this artifact be used to resume builds? |
| `is_final` | BOOLEAN | Is this the final deliverable? |
| `expires_at` | TIMESTAMP | When to clean up temporary artifacts |
| `metadata` | JSONB | Additional metadata (VM IDs, snapshot IDs, etc.) |
| `created_at` | TIMESTAMP | When the artifact was registered |
| `updated_at` | TIMESTAMP | Last update time |
| `deleted_at` | TIMESTAMP | Soft delete timestamp for audit |

**Indexes:**
- `idx_build_artifacts_build_id` - Fast lookups by build
- `idx_build_artifacts_state_code` - Find artifacts by state
- `idx_build_artifacts_type` - Filter by artifact type
- `idx_build_artifacts_resumable` - Find resumable artifacts only
- Unique constraint on `(build_id, artifact_name)`

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

### Managing Build Artifacts (Full Registry)

The Build Artifacts API provides comprehensive artifact lifecycle management for resumable builds.

#### Creating a Build Artifact

Register an artifact with full metadata and checksum:

**Request:**
```bash
curl -X POST "http://localhost:8080/builds/{build_id}/artifacts" \
  -H "X-API-Key: dev-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "state_code": 20,
    "artifact_name": "base-vm-snapshot",
    "artifact_type": "vm_snapshot",
    "artifact_path": "s3://my-builds/project-123/build-456/state-20/snapshot.qcow2",
    "storage_backend": "s3",
    "storage_region": "us-east-1",
    "storage_bucket": "my-builds",
    "storage_key": "project-123/build-456/state-20/snapshot.qcow2",
    "size_bytes": 2147483648,
    "checksum": "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
    "checksum_algorithm": "sha256",
    "is_resumable": true,
    "is_final": false,
    "metadata": {
      "vm_id": "vm-abc123",
      "snapshot_id": "snap-xyz789",
      "disk_format": "qcow2",
      "compression": "none"
    }
  }'
```

**Response:**
```json
{
  "id": "artifact-uuid-123",
  "build_id": "build-uuid-456",
  "state_code": 20,
  "artifact_name": "base-vm-snapshot",
  "artifact_type": "vm_snapshot",
  "artifact_path": "s3://my-builds/project-123/build-456/state-20/snapshot.qcow2",
  "storage_backend": "s3",
  "storage_region": "us-east-1",
  "storage_bucket": "my-builds",
  "storage_key": "project-123/build-456/state-20/snapshot.qcow2",
  "size_bytes": 2147483648,
  "checksum": "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
  "checksum_algorithm": "sha256",
  "is_resumable": true,
  "is_final": false,
  "metadata": {
    "vm_id": "vm-abc123",
    "snapshot_id": "snap-xyz789",
    "disk_format": "qcow2",
    "compression": "none"
  },
  "created_at": "2026-02-16T10:30:00Z",
  "updated_at": "2026-02-16T10:30:00Z"
}
```

#### Listing Resumable Artifacts

Find all resumable artifacts for a build (for recovery):

```bash
curl "http://localhost:8080/builds/{build_id}/artifacts?is_resumable=true" \
  -H "X-API-Key: dev-key-12345"
```

**Response:**
```json
[
  {
    "id": "artifact-uuid-123",
    "build_id": "build-uuid-456",
    "state_code": 20,
    "artifact_name": "base-vm-snapshot",
    "artifact_type": "vm_snapshot",
    "artifact_path": "s3://my-builds/...qcow2",
    "storage_backend": "s3",
    "size_bytes": 2147483648,
    "checksum": "abcdef0123...",
    "is_resumable": true,
    "is_final": false,
    "created_at": "2026-02-16T10:30:00Z"
  },
  {
    "id": "artifact-uuid-456",
    "build_id": "build-uuid-456",
    "state_code": 35,
    "artifact_name": "configured-vm-snapshot",
    "artifact_type": "vm_snapshot",
    "artifact_path": "s3://my-builds/...qcow2",
    "storage_backend": "s3",
    "size_bytes": 3221225472,
    "checksum": "fedcba9876...",
    "is_resumable": true,
    "is_final": false,
    "created_at": "2026-02-16T11:15:00Z"
  }
]
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

The BuildState CLI (`bldst`) provides convenient commands for managing artifacts.

### Quick Reference with Build States

Add a build state with artifact information (for basic tracking):

```bash
bldst build add-state {build-id} \
  --state 25 \
  --status completed \
  --storage-type s3 \
  --storage-path "s3://my-builds/project-123/build-456/state-25/base-image.qcow2" \
  --artifact-size 2147483648 \
  --checksum "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789"
```

### Full Artifact Management (Recommended for Resumable Builds)

#### Register a New Artifact

```bash
# After uploading an artifact to storage, register it in the system
bldst artifact create {build-id} \
  --name "base-vm-snapshot" \
  --type "vm_snapshot" \
  --path "s3://my-builds/project-123/build-456/state-20/snapshot.qcow2" \
  --state 20 \
  --backend "s3" \
  --region "us-east-1" \
  --bucket "my-builds" \
  --key "project-123/build-456/state-20/snapshot.qcow2" \
  --size 2147483648 \
  --checksum "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789" \
  --resumable
```

#### List All Artifacts for a Build

```bash
bldst artifact list {build-id}
```

#### List Only Resumable Artifacts (for Recovery)

```bash
# Find artifacts that can be used to resume a failed build
bldst artifact list-resumable {build-id}
```

**Example Output:**
```
┌──────────────┬───────────────────┬─────────────┬────────────┬──────────┐
│ Artifact ID  │ Name              │ Type        │ State Code │ Size     │
├──────────────┼───────────────────┼─────────────┼────────────┼──────────┤
│ abc123...    │ base-vm-snapshot  │ vm_snapshot │ 20         │ 2.0 GB   │
│ def456...    │ configured-vm     │ vm_snapshot │ 35         │ 3.0 GB   │
└──────────────┴───────────────────┴─────────────┴────────────┴──────────┘
```

#### Get Artifact Details

```bash
bldst artifact get {build-id} {artifact-id}
```

**Example Output:**
```json
{
  "id": "abc123...",
  "build_id": "build-uuid-456",
  "state_code": 20,
  "artifact_name": "base-vm-snapshot",
  "artifact_type": "vm_snapshot",
  "artifact_path": "s3://my-builds/project-123/build-456/state-20/snapshot.qcow2",
  "storage_backend": "s3",
  "storage_region": "us-east-1",
  "size_bytes": 2147483648,
  "checksum": "abcdef01234...",
  "checksum_algorithm": "sha256",
  "is_resumable": true,
  "is_final": false,
  "metadata": {
    "vm_id": "vm-abc123",
    "snapshot_id": "snap-xyz789"
  },
  "created_at": "2026-02-16T10:30:00Z"
}
```

#### Update Artifact Metadata

```bash
# Mark an artifact as final when build completes
bldst artifact update {build-id} {artifact-id} \
  --final \
  --name "rhel-9-base-final"
```

### CLI Parameters

| Parameter | Description | Required |
|-----------|-------------|----------|
| `--name` | Unique artifact name within the build | Yes |
| `--type` | Artifact type (vm_snapshot, ami, disk_image, etc.) | Yes |
| `--path` | Full path/URI to the stored artifact | Yes |
| `--state` | State code at which artifact was created | Yes |
| `--backend` | Storage backend (s3, azure_blob, gcp_storage, etc.) | Yes |
| `--region` | Storage region | No |
| `--bucket` | Storage bucket or container name | No |
| `--key` | Storage key/path within bucket | No |
| `--size` | Size in bytes | No |
| `--checksum` | SHA256 checksum | No |
| `--checksum-algorithm` | Checksum algorithm (default: sha256) | No |
| `--resumable` | Mark as resumable (default: true) | No |
| `--final` | Mark as final deliverable | No |

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
