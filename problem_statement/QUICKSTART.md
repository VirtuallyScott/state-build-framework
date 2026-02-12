# State-Based Build Framework: Quick Start Guide

## Overview

This framework introduces state codes (0-100, incrementing by 5) for resumable multi-cloud IaaS image builds. Failed builds stay at their failed state and retry, rather than starting over completely.

**Key Benefits:**
- Resumable pipelines (no lost progress)
- Cross-platform status communication
- Scalable state numbering
- Intelligent failure handling
- **Centralized tracking** via FastAPI service
- **CLI tooling** for easy management
- **Dashboard and reporting** capabilities

## Architecture Overview

The framework consists of three main components:

1. **FastAPI Service** (`api_service/`) - REST API for build state tracking, user management, and reporting
2. **CLI Tool** (`buildstate_cli/`) - Command-line interface for interacting with the service
3. **Documentation** (`problem_statement/`) - Framework concepts and implementation guides

## 1. Quick Setup

### Start the Services
```bash
cd api_service
make up  # Starts API service with PostgreSQL and Redis
```

### Install CLI Tool
```bash
cd buildstate_cli
pip install -e .
```

### Verify Installation
```bash
# Check API service health
curl http://localhost:8000/health

# Check CLI tool
bldst --help
```

## 2. Create Your First Build

### Using the CLI (Recommended)
```bash
# Create a user
bldst user create --username "builder" --email "builder@example.com"

# Create an API token
bldst token create --username "builder" --description "Build pipeline token"

# Start a new build
bldst build create --platform "aws" --image-type "rhel8" --description "RHEL 8 base image"

# Update build state
bldst build update <build-id> --state 10 --status "completed"
```

### Using curl (Not Recommended for Production)
```bash
# Create a build (curl example - use CLI instead)
curl -X POST http://localhost:8000/builds \
  -H "Content-Type: application/json" \
  -d '{"platform": "aws", "image_type": "rhel8", "description": "RHEL 8 base image"}'
```

## 3. State Code System

State codes range from 0 (nothing) to 100 (complete), incrementing by 5:

| State | Description | Notes |
|-------|-------------|-------|
| 0 | Initial state | Pipeline triggered |
| 5-45 | Infrastructure setup | OS, networking, security |
| 50-80 | Application deployment | Services, configuration |
| 85-95 | Testing and validation | Quality assurance |
| 100 | Complete and delivered | Image published |

## 4. Integration with Build Pipelines

### Concourse CI Example
```yaml
- task: update-build-state
  config:
    platform: linux
    image_resource:
      type: docker-image
      source: { repository: python, tag: "3.11" }
    inputs:
    - name: buildstate-cli
    run:
      path: buildstate-cli/bldst_cli
      args:
      - build
      - update
      - ((build-id))
      - --state
      - "10"
      - --status
      - "completed"
```

### GitHub Actions Example
```yaml
- name: Update Build State
  run: |
    bldst_cli build update ${{ env.BUILD_ID }} --state 10 --status completed
```

## 5. Monitoring and Reporting

### Health Checks
```bash
# API service health
curl http://localhost:8000/health

# Readiness check
curl http://localhost:8000/ready

# Status overview
curl http://localhost:8000/status
```

### CLI Reporting
```bash
# List all builds
bldst build list

# Get build details
bldst build get <build-id>

# View state history
bldst build history <build-id>
```

## 6. Production Deployment

### Docker Compose (Recommended)
```bash
cd api_service
docker-compose -f docker/docker-compose.yml up -d
```

### Environment Variables
```bash
# API Service
export DATABASE_URL="postgresql://user:pass@localhost:5432/builds"
export REDIS_URL="redis://localhost:6379"
export SECRET_KEY="your-secret-key"

# CLI Tool
export BUILDSTATE_API_URL="http://localhost:8000"
export BUILDSTATE_API_TOKEN="your-api-token"
```

## 7. Best Practices

### State Management
- **Always advance states** on successful completion
- **Stay at current state** on failure (don't rollback)
- **Use descriptive status messages** for debugging
- **Implement retry logic** at the pipeline level

### Security
- **Use API tokens** instead of basic auth
- **Rotate tokens regularly** for production use
- **Enable HTTPS** in production deployments
- **Use environment variables** for secrets

### Monitoring
- **Monitor state transitions** for pipeline health
- **Alert on stuck builds** (same state for too long)
- **Track build success rates** by platform/image type
- **Use dashboards** for visibility into build pipelines

## 8. Troubleshooting

### Common Issues
```bash
# API service not responding
curl http://localhost:8000/health

# CLI authentication issues
bldst_cli auth login

# Database connection problems
cd api_service && make logs
```

### Debug Mode
```bash
# Enable debug logging
export BUILDSTATE_DEBUG=1
bldst --verbose build list
```

## Next Steps

1. **Read the complete framework guide**: `README.md`
2. **Explore sample implementations**: `sample-implementation.md`
3. **Understand failure handling**: `failure-handling.md`
4. **Customize for your cloud provider**: See state definitions in `states.md`

---

**Framework Version**: 1.0
**Last Updated**: February 12, 2026
    timestamp DATETIME NOT NULL,
    status TEXT NOT NULL,
    error_message TEXT
);
```

### Initialize Build
```bash
#!/bin/bash
BUILD_ID="my-image-build-$(date +%s)"
CLOUD_PROVIDER="aws"
IMAGE_TYPE="rhel8-webserver"

sqlite3 /var/lib/state-builds/$BUILD_ID.db << EOF
INSERT INTO builds (build_id, current_state, cloud_provider, image_type, start_time, last_update, status)
VALUES ('$BUILD_ID', 0, '$CLOUD_PROVIDER', '$IMAGE_TYPE', datetime('now'), datetime('now'), 'running');
EOF
```

## 3. State Code Reference

| State | Description | Key Actions |
|-------|-------------|-------------|
| 0 | Initial state | Pipeline triggered |
| 5 | Kickstart initiated | Packer starts OS install |
| 10 | Green image created | Bootable image with SSH access |
| 15 | Base configuration | Basic system setup |
| 20 | Cloud provider setup | AWS/Azure/GCP specific config |
| 25 | Security baseline | Firewall, SELinux, patches |
| 30 | Monitoring setup | Install monitoring agents |
| 35 | Runtime prerequisites | Java, Python, Node.js |
| 40 | Network configuration | DNS, proxies, VPN |
| 45 | Storage configuration | Disks, mount points |
| 50 | User management | Additional users, auth |
| 55 | Service installation | Web servers, databases |
| 60 | Application deployment | Deploy applications |
| 65 | Config management | Environment configs |
| 70 | Integration testing | Basic functionality tests |
| 75 | Performance optimization | Tuning, caching |
| 80 | Backup setup | Backup agents, snapshots |
| 85 | Documentation | Update metadata |
| 90 | Final validation | Comprehensive tests |
| 95 | Image sealing | Cleanup, finalize |
| 100 | Complete and delivered | Published and available |

## 4. Implement State Updates

### Core Functions
```bash
# Update state on success (advance to next)
update_state_success() {
    local build_id=$1
    local completed_state=$2
    local next_state=$((completed_state + 5))

    sqlite3 /var/lib/state-builds/$build_id.db << EOF
    UPDATE builds SET current_state = $next_state, last_update = datetime('now'), status = 'running' WHERE build_id = '$build_id';
    INSERT INTO state_history (build_id, state, timestamp, status, error_message)
    VALUES ('$build_id', $completed_state, datetime('now'), 'completed', '');
EOF
}

# Update state on failure (stay at current state)
update_state_failure() {
    local build_id=$1
    local failed_state=$2
    local error_msg=$3

    sqlite3 /var/lib/state-builds/$build_id.db << EOF
    UPDATE builds SET last_update = datetime('now'), status = 'failed' WHERE build_id = '$build_id';
    INSERT INTO state_history (build_id, state, timestamp, status, error_message)
    VALUES ('$build_id', $failed_state, datetime('now'), 'failed', '$error_msg');
EOF
}
```

## 5. Integrate with Your Tools

### Packer Integration
```hcl
# In your packer.json
{
  "builders": [{
    "type": "amazon-ebs",
    "ami_name": "my-image-{{timestamp}}"
  }],
  "provisioners": [{
    "type": "shell",
    "inline": [
      "bldst_cli build update ${BUILD_ID} --state 10 --status completed --message 'Packer provisioner completed'"
    ]
  }]
}
```

### Ansible Integration
```yaml
# In your playbook.yml
- name: Update state after task completion
  hosts: all
  tasks:
    - name: Install packages
      yum:
        name: httpd
        state: present

    - name: Mark state 55 as completed
      command: bldst_cli build update {{ build_id }} --state 55 --status completed --message "Application deployment completed"
      when: not ansible_failed_tasks
```

### Concourse Pipeline
```yaml
jobs:
- name: build-image
  plan:
  - task: check-state
    config:
      run:
        path: ./scripts/check-build-state.sh
  - task: packer-build
    config:
      run:
        path: packer/build.sh
    on_success: &update-state
      put: state-store
      params: {file: state.json}
    on_failure: *update-state
```

## 6. Handle Failures and Resumes

### Failure Handling Rules
1. **Stay at failed state** (don't rollback to 0)
2. **Mark status as "failed"** but preserve state code
3. **Retry failed state** up to 3 times
4. **Require manual intervention** after max retries

### Resume Logic
```bash
resume_build() {
    local build_id=$1

    # Get current state and status
    local current_state=$(get_current_state $build_id)
    local status=$(get_build_status $build_id)

    if [ "$status" = "failed" ]; then
        echo "Retrying failed state $current_state"
        retry_state $build_id $current_state
    elif [ "$status" = "running" ]; then
        echo "Continuing from state $current_state"
        run_next_state $build_id $current_state
    fi
}
```

## 7. Sample AWS RHEL 8 Implementation

### Directory Structure
```
my-image-build/
├── packer/
│   ├── rhel8.json
│   └── kickstart.cfg
├── ansible/
│   ├── inventory/
│   ├── playbooks/
│   │   ├── 15-base-config.yml
│   │   ├── 20-aws-setup.yml
│   │   └── ...
│   └── roles/
├── scripts/
│   ├── init-build.sh
│   ├── update-state.sh
│   └── resume-build.sh
├── concourse/
│   └── pipeline.yml
└── state/
    └── builds.db
```

### Key Scripts

#### update-state.sh
```bash
#!/bin/bash
BUILD_ID=$1
STATE=$2
STATUS=${3:-completed}
ERROR_MSG=${4:-}

DB_PATH="/var/lib/state-builds/${BUILD_ID}.db"

if [ "$STATUS" = "completed" ]; then
    NEXT_STATE=$((STATE + 5))
    sqlite3 $DB_PATH << EOF
    UPDATE builds SET current_state = $NEXT_STATE, last_update = datetime('now'), status = 'running' WHERE build_id = '$BUILD_ID';
    INSERT INTO state_history (build_id, state, timestamp, status, error_message)
    VALUES ('$BUILD_ID', $STATE, datetime('now'), 'completed', '');
EOF
elif [ "$STATUS" = "failed" ]; then
    sqlite3 $DB_PATH << EOF
    UPDATE builds SET last_update = datetime('now'), status = 'failed' WHERE build_id = '$BUILD_ID';
    INSERT INTO state_history (build_id, state, timestamp, status, error_message)
    VALUES ('$BUILD_ID', $STATE, datetime('now'), 'failed', '$ERROR_MSG');
EOF
fi

# Sync to S3 if configured
aws s3 cp $DB_PATH s3://state-builds/aws/$BUILD_ID/state.db
```

#### resume-build.sh
```bash
#!/bin/bash
BUILD_ID=$1

# Download state if needed
if [ ! -f "/var/lib/state-builds/${BUILD_ID}.db" ]; then
    aws s3 cp s3://state-builds/aws/$BUILD_ID/state.db /var/lib/state-builds/${BUILD_ID}.db
fi

CURRENT_STATE=$(sqlite3 /var/lib/state-builds/${BUILD_ID}.db "SELECT current_state FROM builds WHERE build_id = '$BUILD_ID';")
STATUS=$(sqlite3 /var/lib/state-builds/${BUILD_ID}.db "SELECT status FROM builds WHERE build_id = '$BUILD_ID';")

case $STATUS in
    "failed")
        echo "Retrying failed state $CURRENT_STATE"
        run_state_task $BUILD_ID $CURRENT_STATE
        ;;
    "running")
        NEXT_STATE=$((CURRENT_STATE + 5))
        echo "Continuing to state $NEXT_STATE"
        run_state_task $BUILD_ID $NEXT_STATE
        ;;
esac
```

## 8. Monitor and Debug

### Check Build Status
```bash
# Current state and status
sqlite3 /var/lib/state-builds/${BUILD_ID}.db "
SELECT current_state, status, last_update FROM builds WHERE build_id = '${BUILD_ID}';
"

# State history
sqlite3 /var/lib/state-builds/${BUILD_ID}.db "
SELECT state, timestamp, status, error_message FROM state_history
WHERE build_id = '${BUILD_ID}' ORDER BY timestamp DESC LIMIT 10;
"
```

### Common Issues
- **State not advancing**: Check if update-state.sh is called after successful tasks
- **Resume not working**: Verify database file exists and has correct permissions
- **Cloud sync failing**: Check AWS credentials and S3 bucket permissions

## 9. Migration from Current System

### Phase 1: Add State Tracking
```bash
# Add state calls to existing scripts
# Keep current "start over" logic
# Build history for analysis
```

### Phase 2: Selective Retry
```bash
# Retry expensive operations (kickstart, downloads)
# Keep "start over" for fast operations
```

### Phase 3: Full Resumability
```bash
# All states support resume/retry
# Intelligent retry strategies per state type
```

## 10. Best Practices

### State Management
- Always call update-state.sh after state completion
- Use "in_progress" status for long-running operations
- Include meaningful error messages in failure updates

### Error Handling
- Implement exponential backoff for retries
- Set maximum retry limits per state
- Alert on repeated failures at same state

### Storage
- Use SQLite for local performance
- Sync to cloud storage after each state change
- Implement backup and retention policies

### Testing
- Test failure scenarios explicitly
- Verify resume functionality
- Validate state transitions

## Next Steps

1. **Start small**: Implement for one image type on one cloud
2. **Add monitoring**: Track state transitions and failure rates
3. **Expand gradually**: Add more cloud providers and image types
4. **Automate**: Build dashboards and alerting around state metrics

## Support

For detailed documentation, see:
- `README.md` - Complete framework guide
- `sample-implementation.md` - Full AWS example
- `failure-handling.md` - Failure handling details

---

**Framework Version**: 1.0
**Last Updated**: February 12, 2026