# State Storage Implementation Guide

This document provides implementation details for storing and managing build state across the State-Based Build Framework.

## Storage Options Comparison

| Storage Type | Pros | Cons | Best For |
|-------------|------|------|----------|
| SQLite | ACID compliant, SQL queries, no external deps, fast | Single-writer, file locking issues | Local/single-worker pipelines |
| JSON File | Simple, human-readable, easy backup | No concurrency, manual locking | Simple deployments, read-heavy |
| DynamoDB | Highly available, scalable, concurrency control | Vendor lock-in, AWS-only | AWS primary, multi-cloud secondary |
| CosmosDB | Global distribution, multi-model | Azure-only, complex setup | Azure primary ecosystems |
| S3/Blob Storage | Durable, versioned, accessible anywhere | Eventual consistency, no transactions | Backup, archive, simple state |
| Local JSON + Cloud Backup | Fast local + durable remote | Sync complexity | Hybrid environments |

## Recommended Implementation: Hybrid SQLite + S3

For maximum flexibility across cloud providers, we recommend a hybrid approach:

### Local SQLite Database
- **Location**: `/var/lib/state-builds/{buildId}.db`
- **Purpose**: Fast, transactional state updates during build
- **Schema**:

```sql
CREATE TABLE builds (
    build_id TEXT PRIMARY KEY,
    current_state INTEGER NOT NULL,
    cloud_provider TEXT NOT NULL,
    image_type TEXT NOT NULL,
    start_time DATETIME NOT NULL,
    last_update DATETIME NOT NULL,
    status TEXT NOT NULL, -- 'running', 'completed', 'failed'
    metadata TEXT, -- JSON blob
    resume_token TEXT
);

CREATE TABLE state_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    build_id TEXT NOT NULL,
    state INTEGER NOT NULL,
    timestamp DATETIME NOT NULL,
    status TEXT NOT NULL, -- 'started', 'completed', 'failed'
    error_message TEXT,
    FOREIGN KEY (build_id) REFERENCES builds(build_id)
);

CREATE TABLE state_metadata (
    build_id TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT,
    PRIMARY KEY (build_id, key),
    FOREIGN KEY (build_id) REFERENCES builds(build_id)
);
```

### Cloud Backup (S3/Blob Storage)
- **Location**: `s3://state-builds/{cloud-provider}/{buildId}/state.json`
- **Purpose**: Durable backup, cross-environment access
- **Sync**: Upload after each state change, download on resume

## State Management API

### Core Functions

```bash
# Initialize new build
init_build() {
    local build_id=$1
    local cloud_provider=$2
    local image_type=$3
    
    sqlite3 /var/lib/state-builds/$build_id.db << EOF
    INSERT INTO builds (build_id, current_state, cloud_provider, image_type, start_time, last_update, status)
    VALUES ('$build_id', 0, '$cloud_provider', '$image_type', datetime('now'), datetime('now'), 'running');
EOF
}

# Update state - SUCCESSFUL COMPLETION
update_state_success() {
    local build_id=$1
    local completed_state=$2
    
    sqlite3 /var/lib/state-builds/$build_id.db << EOF
    UPDATE builds SET current_state = $completed_state, last_update = datetime('now'), status = 'running' WHERE build_id = '$build_id';
    INSERT INTO state_history (build_id, state, timestamp, status, error_message)
    VALUES ('$build_id', $completed_state, datetime('now'), 'completed', '');
EOF
    
    # Sync to cloud
    sync_to_cloud $build_id
}

# Update state - FAILURE (stay at current state)
update_state_failure() {
    local build_id=$1
    local failed_state=$2
    local error_msg=$3
    
    sqlite3 /var/lib/state-builds/$build_id.db << EOF
    UPDATE builds SET last_update = datetime('now'), status = 'failed' WHERE build_id = '$build_id';
    INSERT INTO state_history (build_id, state, timestamp, status, error_message)
    VALUES ('$build_id', $failed_state, datetime('now'), 'failed', '$error_msg');
EOF
    
    # Sync to cloud
    sync_to_cloud $build_id
}

# Get current state and status
get_build_status() {
    local build_id=$1
    sqlite3 /var/lib/state-builds/$build_id.db "SELECT current_state, status FROM builds WHERE build_id = '$build_id';"
}

# Resume build - check if current state needs retry
resume_build() {
    local build_id=$1
    
    # Check if local DB exists
    if [ ! -f /var/lib/state-builds/$build_id.db ]; then
        # Download from cloud
        download_from_cloud $build_id
    fi
    
    local current_state=$(sqlite3 /var/lib/state-builds/$build_id.db "SELECT current_state FROM builds WHERE build_id = '$build_id';")
    local status=$(sqlite3 /var/lib/state-builds/$build_id.db "SELECT status FROM builds WHERE build_id = '$build_id';")
    
    echo "Build $build_id at state $current_state with status $status"
    
    if [ "$status" = "completed" ] && [ "$current_state" -eq 100 ]; then
        echo "Build already completed successfully"
        exit 0
    elif [ "$status" = "failed" ]; then
        echo "Build failed at state $current_state, attempting retry..."
        retry_state $build_id $current_state
    else
        # Continue from current state
        run_state_task $build_id $current_state
    fi
}
```

### Cloud Sync Functions

```bash
# AWS S3
sync_to_cloud() {
    local build_id=$1
    local cloud_provider=$(get_cloud_provider $build_id)
    
    # Export to JSON
    sqlite3 /var/lib/state-builds/$build_id.db -json << 'EOF' > /tmp/state.json
    SELECT json_object(
        'buildId', b.build_id,
        'currentState', b.current_state,
        'cloudProvider', b.cloud_provider,
        'imageType', b.image_type,
        'startTime', b.start_time,
        'lastUpdate', b.last_update,
        'status', b.status,
        'stateHistory', json_group_array(
            json_object(
                'state', h.state,
                'timestamp', h.timestamp,
                'status', h.status,
                'errorMessage', h.error_message
            )
        )
    ) as state_json
    FROM builds b
    LEFT JOIN state_history h ON b.build_id = h.build_id
    WHERE b.build_id = '$build_id'
    GROUP BY b.build_id;
EOF
    
    aws s3 cp /tmp/state.json s3://state-builds/$cloud_provider/$build_id/state.json
}

download_from_cloud() {
    local build_id=$1
    local cloud_provider=$2
    
    aws s3 cp s3://state-builds/$cloud_provider/$build_id/state.json /tmp/state.json
    
    # Import to SQLite (would need a more complex script)
    # This is simplified - real implementation would parse JSON and insert
}
```

## Concourse Pipeline Integration

### Pipeline YAML Structure

```yaml
resources:
- name: state-store
  type: s3
  source:
    bucket: state-builds
    access_key_id: ((aws_access_key))
    secret_access_key: ((aws_secret_key))

jobs:
- name: build-image
  plan:
  - get: source-code
  - get: state-store
    trigger: false
  - task: init-state
    config:
      inputs: [source-code]
      outputs: [state-db]
      run:
        path: ./scripts/init-build-state.sh
    params:
      BUILD_ID: ((build_id))
      CLOUD_PROVIDER: aws
      IMAGE_TYPE: rhel8-webserver
  - task: kickstart
    config:
      run:
        path: ./scripts/run-kickstart.sh
    on_success:
      put: state-store
      params:
        file: state-db/state.json
        acl: private
    on_failure:
      put: state-store
      params:
        file: state-db/state.json
        acl: private
  - task: ansible-base-config
    config:
      run:
        path: ./scripts/run-ansible.sh
        args: [base-config]
    on_success: &update-state
      put: state-store
      params:
        file: state-db/state.json
        acl: private
    on_failure: *update-state
  # ... continue for each state
```

### State Check Task

```bash
#!/bin/bash
# check-build-state.sh

BUILD_ID=$1
CLOUD_PROVIDER=$2

# Check if state file exists in S3
if aws s3 ls s3://state-builds/$CLOUD_PROVIDER/$BUILD_ID/state.json > /dev/null 2>&1; then
    echo "Found existing state for build $BUILD_ID"
    
    # Download and check current state
    aws s3 cp s3://state-builds/$CLOUD_PROVIDER/$BUILD_ID/state.json /tmp/current-state.json
    
    CURRENT_STATE=$(jq -r '.currentState' /tmp/current-state.json)
    STATUS=$(jq -r '.status' /tmp/current-state.json)
    
    if [ "$STATUS" = "completed" ] && [ "$CURRENT_STATE" -eq 100 ]; then
        echo "Build already completed"
        exit 0
    elif [ "$STATUS" = "failed" ]; then
        echo "Build failed at state $CURRENT_STATE, attempting resume"
        # Set Concourse metadata for resume
        echo "RESUME_STATE=$CURRENT_STATE" > resume-metadata
    else
        echo "Build in progress at state $CURRENT_STATE"
        exit 1  # Fail pipeline to prevent duplicate work
    fi
else
    echo "No existing state found, starting new build"
fi
```

## Ansible Integration

### State Update Callback

Create an Ansible callback plugin to automatically update state on task completion:

```python
# callback/state_update.py
from ansible.plugins.callback import CallbackBase
import sqlite3
import os

class CallbackModule(CallbackBase):
    def __init__(self):
        self.build_id = os.environ.get('BUILD_ID')
        self.db_path = f'/var/lib/state-builds/{self.build_id}.db'
        
    def v2_playbook_on_stats(self, stats):
        # Update state when playbook completes
        if stats.failures == 0:
            self.update_state('completed')
        else:
            self.update_state('failed', f'Playbook failed: {stats.failures} failures')
    
    def update_state(self, status, error_msg=''):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get current state and increment
        cursor.execute('SELECT current_state FROM builds WHERE build_id = ?', (self.build_id,))
        current_state = cursor.fetchone()[0]
        new_state = min(current_state + 5, 100)  # Increment by 5
        
        cursor.execute('''
            UPDATE builds SET current_state = ?, last_update = datetime('now') WHERE build_id = ?
        ''', (new_state, self.build_id))
        
        cursor.execute('''
            INSERT INTO state_history (build_id, state, timestamp, status, error_message)
            VALUES (?, ?, datetime('now'), ?, ?)
        ''', (self.build_id, new_state, status, error_msg))
        
        conn.commit()
        conn.close()
```

### Ansible Usage

```yaml
# playbook.yml
- hosts: all
  environment:
    BUILD_ID: "{{ lookup('env', 'BUILD_ID') }}"
  tasks:
  - name: Update package cache
    apt:
      update_cache: yes
    notify: update_state
    
  handlers:
  - name: update_state
    command: /usr/local/bin/update-build-state.sh {{ BUILD_ID }} 15 completed
```

## Monitoring and Alerting

### State Transition Monitoring

```bash
# monitor-state-transitions.sh
#!/bin/bash

BUILD_ID=$1
EXPECTED_STATE=$2
TIMEOUT=$3

START_TIME=$(date +%s)
while true; do
    CURRENT_STATE=$(get_current_state $BUILD_ID)
    
    if [ "$CURRENT_STATE" -ge "$EXPECTED_STATE" ]; then
        echo "State transition completed: $CURRENT_STATE"
        exit 0
    fi
    
    CURRENT_TIME=$(date +%s)
    ELAPSED=$((CURRENT_TIME - START_TIME))
    
    if [ "$ELAPSED" -gt "$TIMEOUT" ]; then
        echo "Timeout waiting for state transition to $EXPECTED_STATE"
        exit 1
    fi
    
    sleep 30
done
```

### Alerting Integration

Integrate with monitoring systems:

```bash
# Send alert on state transition
send_alert() {
    local build_id=$1
    local state=$2
    local status=$3
    
    # Send to Slack, email, etc.
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"Build $build_id reached state $state with status $status\"}" \
        $SLACK_WEBHOOK_URL
}
```

## Error Handling and Recovery

### Failure Handling Strategy

**Key Principle**: On failure, maintain the current state code but mark the build status as "failed". This preserves progress indication while clearly identifying the failure point.

#### State Transition Examples

```bash
# Example: State 5 (Kickstart) Failure
Current State: 5 (Kickstart initiated)
Action: Kickstart fails due to network timeout
Result: 
- State remains: 5
- Status becomes: "failed"
- History records: state=5, status="failed", error_message="Network timeout during OS install"

# On Resume/Retry:
- System detects failed state 5
- Attempts kickstart again
- If successful: advances to state 10, status="running"
- If fails again: stays at state 5, status="failed", increments retry count
```

#### Why This Approach?

1. **Progress Preservation**: You know the build got past state 0, even if state 5 failed
2. **Clear Failure Points**: Failed states are easily identified for debugging
3. **Retry-Friendly**: Same state can be attempted multiple times
4. **No Rollback Confusion**: Avoids losing progress indication
5. **Manual Intervention**: Failed states can be investigated before retry

### Automatic Retry Logic

```bash
retry_state() {
    local build_id=$1
    local failed_state=$2
    local max_retries=3
    local retry_count=$(get_retry_count $build_id $failed_state)
    
    if [ "$retry_count" -ge "$max_retries" ]; then
        echo "Max retries exceeded for state $failed_state"
        notify_failure $build_id $failed_state
        return 1
    fi
    
    echo "Retry attempt $((retry_count + 1)) for state $failed_state"
    
    # Reset status to running for retry
    update_build_status $build_id "running"
    
    if run_state_task $build_id $failed_state; then
        update_state_success $build_id $((failed_state + 5))
        return 0
    else
        update_state_failure $build_id $failed_state "Retry $((retry_count + 1)) failed"
        increment_retry_count $build_id $failed_state
        return 1
    fi
}

get_retry_count() {
    local build_id=$1
    local state=$2
    sqlite3 /var/lib/state-builds/$build_id.db "
        SELECT COUNT(*) FROM state_history 
        WHERE build_id = '$build_id' AND state = $state AND status = 'failed'
    "
}
```

### State-Specific Retry Strategies

Different states may require different retry approaches:

```bash
run_state_with_retry() {
    local build_id=$1
    local state=$2
    
    case $state in
        5)  # Kickstart - infrastructure issues, retry with backoff
            retry_with_backoff $build_id $state 300 1800  # 5min to 30min delays
            ;;
        10) # Green image validation - quick retry
            retry_immediate $build_id $state 5 60  # 5 attempts, 1min apart
            ;;
        70) # Integration testing - may need manual intervention
            retry_with_notification $build_id $state 2 3600  # 2 retries, 1hr apart
            ;;
        *)  # Default retry strategy
            retry_standard $build_id $state
            ;;
    esac
}
```

### Manual Intervention Workflow

For failures requiring human intervention:

```bash
# Check for failed builds needing attention
check_failed_builds() {
    sqlite3 /var/lib/state-builds/*.db "
        SELECT build_id, current_state, last_update 
        FROM builds 
        WHERE status = 'failed' 
        AND last_update < datetime('now', '-1 hour')
        ORDER BY last_update DESC
    "
}

# Manual retry after investigation
manual_retry() {
    local build_id=$1
    local state=$2
    local reason=$3
    
    # Log manual intervention
    sqlite3 /var/lib/state-builds/$build_id.db "
        INSERT INTO state_history (build_id, state, timestamp, status, error_message)
        VALUES ('$build_id', $state, datetime('now'), 'manual_retry', 'Manual retry: $reason');
    "
    
    # Reset and retry
    update_build_status $build_id "running"
    run_state_task $build_id $state
}
```

### Failure Categories

**Transient Failures** (automatic retry):
- Network timeouts
- Temporary resource unavailability
- Service rate limiting
- Temporary credential issues

**Persistent Failures** (manual intervention):
- Configuration errors
- Missing dependencies
- Security policy violations
- Resource quota exceeded
- Code/logic errors

**State-Specific Failures**:
- State 5: Packer/infrastructure issues
- State 10-65: Ansible playbook failures
- State 70-90: Testing/validation failures
- State 95-100: Publishing/deployment failures

### State Rollback

For critical failures, implement rollback to previous stable state:

```bash
rollback_state() {
    local build_id=$1
    local target_state=$2
    
    # Find last successful state before current
    LAST_SUCCESSFUL=$(sqlite3 /var/lib/state-builds/$build_id.db "
        SELECT state FROM state_history 
        WHERE build_id = '$build_id' AND status = 'completed' 
        ORDER BY timestamp DESC LIMIT 1 OFFSET 1
    ")
    
    if [ -n "$LAST_SUCCESSFUL" ]; then
        update_state $build_id $LAST_SUCCESSFUL completed "Rolled back from failed state"
        echo "Rolled back to state $LAST_SUCCESSFUL"
    fi
}
```

## Performance Considerations

### Database Optimization

```sql
-- Create indexes for performance
CREATE INDEX idx_state_history_build_id ON state_history(build_id);
CREATE INDEX idx_state_history_timestamp ON state_history(timestamp);
CREATE INDEX idx_builds_status ON builds(status);

-- Use WAL mode for better concurrency
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
```

### Caching

- Cache state in memory for frequent reads
- Use Redis for distributed caching in multi-worker setups
- Implement state cache invalidation on updates

### Backup Strategy

- Continuous backup to cloud storage
- Point-in-time recovery capability
- Retention policy: keep all states for 30 days, weekly snapshots for 1 year

## Security Considerations

### Access Control
- Encrypt state database at rest
- Use IAM roles for cloud storage access
- Implement least-privilege access for build workers

### Data Protection
- Sanitize error messages (no secrets in logs)
- Encrypt sensitive metadata
- Implement audit logging for state changes

### Compliance
- Maintain state history for compliance auditing
- Implement data retention policies
- Support for GDPR/data protection requirements