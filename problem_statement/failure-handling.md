# Failure Handling in State-Based Builds

## The Question
When a state fails (e.g., state 5 "kickstart initiated"), what should happen?

Options considered:
1. Return to state 0 (start over completely)
2. Stay at state 0 (reset progress)
3. Use "5-" or sub-states to indicate partial completion

## Recommended Approach: Stay at Failed State

**If state 5 fails → Stay at state 5, mark as "failed"**

### Why This Works Better Than Starting Over

Your current system starts completely over on any failure. This works for fast, simple builds. However, for complex image creation:

**Current Approach Problems**:
- Kickstart takes 15-30 minutes
- Large package downloads take time
- Cloud resource provisioning has delays
- Starting over loses all progress

**State-Based Approach Benefits**:
- Failed state 5 can be retried immediately
- You know you got past state 0 (progress preserved)
- Failure reasons are logged for debugging
- Expensive operations aren't repeated unnecessarily

### Example: Kickstart Failure

```
Timeline:
10:00 - Build starts, reaches state 5 (kickstart initiated)
10:15 - Kickstart fails due to network timeout
10:16 - State remains 5, status = "failed"
10:17 - Retry logic attempts state 5 again
10:32 - Kickstart succeeds, advances to state 10
```

**vs. Old Approach**:
```
10:00 - Build starts, reaches state 5
10:15 - Kickstart fails
10:16 - Start over from state 0 (lose 15 minutes)
10:31 - Reach state 5 again
10:46 - Hopefully succeeds this time
```

### State vs. Status: Clear Separation

**State Codes** = Progress milestones achieved
- State 5 means "kickstart was attempted"
- State 10 means "green image was created"

**Status** = Success/failure of that milestone
- "completed" = milestone achieved successfully
- "failed" = milestone attempted but failed
- "in_progress" = milestone currently being worked on

**Failure Record**:
```json
{
  "currentState": 5,
  "status": "failed",
  "stateHistory": [
    {"state": 5, "status": "failed", "error": "Network timeout", "timestamp": "10:15"},
    {"state": 5, "status": "started", "timestamp": "10:17"},
    {"state": 5, "status": "completed", "timestamp": "10:32"}
  ]
}
```

### Migration Strategy

**Phase 1: Add Tracking (No Behavior Change)**
- Track states but keep current "start over" logic
- Build history for analysis

**Phase 2: Selective Retry**
- Retry expensive operations (kickstart, large downloads)
- Keep "start over" for fast operations

**Phase 3: Full Resumability**
- All states support resume/retry
- Intelligent retry strategies per state type

### State-Specific Retry Strategies

Different failures need different handling:

**Transient Failures (Auto-Retry)**:
- Network timeouts
- Temporary resource unavailability
- Service rate limiting

**Persistent Failures (Manual Intervention)**:
- Configuration errors
- Missing dependencies
- Authentication failures

**Expensive Operations (Smart Retry)**:
- State 5 (Kickstart): Retry with backoff, max 3 attempts
- State 10-65 (Ansible): Quick retry, different playbook runs
- State 70-90 (Testing): May need manual fixes

### Implementation

```bash
# On failure - stay at current state
update_state_failure() {
    # State stays the same, status becomes "failed"
    # History records the failure reason
}

# On retry - attempt same state again
retry_state() {
    # Check retry count
    # If under limit, attempt same state
    # If over limit, require manual intervention
}
```

This approach gives you the benefits of resumability while being compatible with your current "start over" philosophy for simpler operations.