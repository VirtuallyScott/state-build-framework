# State-Based Build Framework: Quick Start Guide

## Overview

This framework introduces state codes (0-100, incrementing by 5) for resumable multi-cloud IaaS image builds. Failed builds stay at their failed state and retry, rather than starting over completely.

**Key Benefits:**
- Resumable pipelines (no lost progress)
- Cross-platform status communication
- Scalable state numbering
- Intelligent failure handling

## 1. Choose Your Storage Backend

### Option A: SQLite + S3 (Recommended)
```bash
# Local SQLite for performance, S3 for durability
apt-get install sqlite3 awscli  # or equivalent
```

### Option B: DynamoDB (AWS Native)
```bash
# Use AWS SDK for DynamoDB access
pip install boto3
```

### Option C: JSON Files (Simple)
```bash
# Just need file system access
# Good for testing or single-worker setups
```

## 2. Set Up State Database

### SQLite Schema
```sql
CREATE TABLE builds (
    build_id TEXT PRIMARY KEY,
    current_state INTEGER NOT NULL,
    cloud_provider TEXT NOT NULL,
    image_type TEXT NOT NULL,
    start_time DATETIME NOT NULL,
    last_update DATETIME NOT NULL,
    status TEXT NOT NULL
);

CREATE TABLE state_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    build_id TEXT NOT NULL,
    state INTEGER NOT NULL,
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
      "curl -o /tmp/update-state.sh https://example.com/scripts/update-state.sh",
      "chmod +x /tmp/update-state.sh",
      "BUILD_ID=${BUILD_ID} /tmp/update-state.sh 10 completed"
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
      command: /usr/local/bin/update-state.sh {{ build_id }} 55 completed
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
- `.copilot/README.md` - Complete framework guide
- `.copilot/sample-implementation.md` - Full AWS example
- `.copilot/failure-handling.md` - Failure handling details

---

**Framework Version**: 1.0
**Last Updated**: February 12, 2026