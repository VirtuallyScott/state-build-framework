# Problem Statement: State-Based Build Management

## The Problem

Organizations building infrastructure-as-a-service (IaaS) images face several critical challenges:

### 1. **Build Fragility and Non-Resumability**
- Multi-cloud image builds can take 30-90 minutes or more
- A failure at minute 75 means starting completely over from minute 0
- Network timeouts, package installation failures, or cloud API issues waste hours of compute time
- No visibility into where a build actually failed in complex multi-step processes

### 2. **Lack of Cross-Platform Visibility**
- Different cloud providers (AWS, Azure, GCP, private clouds) use different tools and processes
- No unified way to track build progress across heterogeneous environments
- Pipeline teams struggle to answer "where did this build fail?" across different platforms
- Build state is often locked in proprietary systems or buried in logs

### 3. **Communication Breakdown**
- Build pipelines can't communicate their state to external systems
- Dashboards show "running" or "failed" but not specific progress
- Downstream systems don't know when artifacts are ready for consumption
- Manual checking required to determine build status and readiness

### 4. **Distributed Build Coordination**
- Multiple build servers in a pool can't share work effectively
- Artifacts from one build stage can't be reliably accessed by another server
- No standardized way to track where intermediate artifacts are stored
- Build resumption requires manual intervention and knowledge transfer

### 5. **Scalability and Maintenance**
- Adding new build steps requires renumbering all subsequent steps
- Can't insert steps without breaking existing pipelines
- No clear milestone structure for complex builds
- Hard to maintain consistency across multiple image types and variants

## The Solution: State-Based Build Management Framework

This framework introduces a **standardized state code system** (0-100) with **centralized state tracking** and **artifact management** to solve these challenges.

### Core Components

#### 1. **State Code System (0-100)**
- **Numerical milestones** representing build progress
- **Increments of 5** allow insertion of new states without renumbering
- **Universal across cloud providers** - state 25 means the same thing everywhere
- **Clear completion percentage** - state 50 = 50% complete

**Example State Codes:**
- **0**: Initial state - nothing started
- **10**: Base OS image created (bootable)
- **25**: Security baseline applied
- **50**: Application runtimes installed
- **75**: Testing and validation complete
- **100**: Image published and delivered

#### 2. **FastAPI State Management Service**
- **Centralized state tracking** for all builds across all platforms
- **RESTful API** accessible from any build environment
- **PostgreSQL backend** for reliable state persistence
- **Real-time dashboards** showing build progress across the organization
- **Historical tracking** for trend analysis and optimization

#### 3. **Artifact Storage Tracking**
- **Record artifact locations** when build states complete
- **Support for multiple storage backends** (S3, NFS, EBS, Ceph, etc.)
- **Distributed build server coordination** - any server can resume from any state
- **Checksum verification** ensures artifact integrity
- **Metadata tracking** for artifact details (size, format, compression)

#### 4. **Command-Line Interface (CLI)**
- **Easy integration** with existing CI/CD pipelines
- **Simple state updates** from shell scripts and Ansible playbooks
- **Build lifecycle management** (create, update, query, resume)
- **Authentication handling** with API keys and tokens

## How It Solves the Problems

### ✅ Resumable Builds
**Problem**: Failure at minute 75 = start over from minute 0

**Solution**: 
- State 10 completes and artifact is stored in S3
- State 25 completes and artifact is stored in S3
- State 50 fails  
- **Resume from state 50** using the artifact from state 25
- Only retry the failed portion, saving 50 minutes of work

**Example:**
```bash
# Build fails at state 50
bldst build get {build-id}
# Shows: current_state=50, status=failed

# Retry just state 50
# Downloads artifact from state 25 automatically
# Resumes work without repeating states 0-25
```

### ✅ Universal Progress Tracking
**Problem**: No visibility into build progress across platforms

**Solution**:
- All platforms report to the same API using standard state codes
- Dashboard shows all builds, all platforms, in real-time
- State 35 means "runtime prerequisites installed" everywhere
- Consistent progress reporting across AWS, Azure, GCP, and private clouds

**Example:**
```bash
# From anywhere
bldst build list

# Returns:
# AWS Build #123:    State 45 - Storage configuration (45% complete)
# Azure Build #124:  State 75 - Testing complete (75% complete)  
# GCP Build #125:    State 100 - Delivered (100% complete)
```

### ✅ Artifact Distribution for Distributed Builds
**Problem**: Build Server A creates artifact, Build Server B can't find it

**Solution**:
- Server A completes state 25, uploads artifact to S3, records location in state database
- Server B picks up state 50, queries database for state 25 artifact, downloads from S3
- Any server in the pool can resume any build from any state

**Example:**
```bash
# Server A completes state 25
bldst build add-state {build-id} \
  --state 25 \
  --status completed \
  --storage-type s3 \
  --storage-path "s3://builds/proj-123/build-456/state-25/image.qcow2" \
  --checksum "sha256:abc123..."

# Server B picks up state 50
# Queries API: "Where is the artifact from state 25?"
# Downloads from s3://builds/proj-123/build-456/state-25/image.qcow2
# Verifies checksum
# Continues build
```

### ✅ Scalable State Management
**Problem**: Adding a step between state 40 and 50 requires renumbering

**Solution**:
- States increment by 5 (0, 5, 10, 15, 20, 25...)
- New step? Insert at 42 or 43 or 44
- Existing pipelines unaffected
- No renumbering cascade

**Example:**
```
Original:
  40: Network config
  45: Storage config
  
Need new step for VPN setup?
  40: Network config
  42: VPN setup ← NEW, no renumbering needed
  45: Storage config
```

### ✅ Integration with Existing Tools
**Problem**: Our tools (Packer, Ansible, Concourse) don't track state

**Solution**:
- Lightweight CLI integrates with existing scripts
- Update state from Ansible playbooks, Packer provisioners, shell scripts
- No major refactoring of existing pipelines
- Gradual adoption - start with one pipeline, expand from there

**Example Integration:**
```bash
#!/bin/bash
# Existing Packer build script

# Add: Report state 5 (starting kickstart)
bldst build add-state $BUILD_ID --state 5 --status in_progress

packer build kickstart.pkr.hcl

# Add: Report state 10 (kickstart complete)
bldst build add-state $BUILD_ID --state 10 --status completed \
  --storage-type s3 \
  --storage-path "s3://builds/$BUILD_ID/base-image.qcow2"
  
# Continue with Ansible...
```

## State vs Status: A Key Distinction

The framework separates **state codes** (progress milestones) from **status** (success/failure):

- **State**: WHERE you are in the build process (0-100)
- **Status**: HOW that state attempt went (pending, in_progress, completed, failed)

**Example:**
- Build reaches **state 25** (security baseline)
- Security scan **fails** 
- **State remains 25** (we attempted the milestone)
- **Status becomes "failed"** (we didn't complete it)
- On **retry**, attempt state 25 again
- If **successful**, advance to state 30

This approach ensures:
- ✅ Progress is never lost (you know you reached state 25)
- ✅ Failures are clearly marked for debugging
- ✅ Retry logic knows exactly where to resume
- ✅ History shows multiple attempts with failure reasons

## Real-World Use Cases

### Use Case 1: Multi-Region AWS Build
**Scenario:** Building RHEL 8 images for 6 AWS regions

**Without Framework:**
- Build fails in region 4 after 60 minutes
- Restart from beginning, wait another 60 minutes
- May fail in region 5 this time
- Repeat until all 6 succeed (could take 6+ hours)

**With Framework:**
- State 0-50: Base configuration (once, 30 minutes)
- Upload artifact to S3
- States 60-100: Deploy to each region in parallel
- Region 4 fails? Retry just region 4 from state 60 (10 minutes)
- Other regions continue independently
- Total time: ~40 minutes instead of 6+ hours

### Use Case 2: Distributed SAP Image Build
**Scenario:** Complex SAP HANA image requiring multiple build servers

**Without Framework:**
- Server A builds base OS
- Manually transfer artifact to Server B
- Server B builds SAP layer
- If Server B fails, manual coordination to retry
- No visibility into overall progress

**With Framework:**
- Server A: States 0-30 (base OS), stores artifact to NFS
- API records: state 30 complete, artifact at /mnt/nfs/builds/sap-123/state-30.qcow2
- Server B: Queries API, downloads state 30 artifact, runs states 35-100
- If Server B fails at state 50, Server C can pick up automatically
- Dashboard shows progress across all servers in real-time

### Use Case 3: Azure + AWS Hybrid Cloud
**Scenario:** Same image type needed for both Azure and AWS

**Without Framework:**
- Separate pipelines for each cloud
- No visibility into which cloud is ahead/behind
- Can't compare build times or failure rates
- Manual dashboard construction

**With Framework:**
- States 0-40: Common base image (cloud-agnostic)
- State 45: Branch to cloud-specific configuration
- API tracks both builds with same state codes
- Dashboard shows: "Azure Build 75% complete, AWS Build 80% complete"
- Consistent state meanings across clouds enables comparison

## Benefits Summary

| Problem | Solution | Impact |
|---------|----------|--------|
| Builds start over after failure | Resume from last completed state | 50-80% time savings on retry |
| No cross-platform visibility | Universal state codes + centralized tracking | Single dashboard for all clouds |
| Can't find artifacts | Artifact storage tracking in state database | Any server can resume any build |
| Hard to add new steps | State codes increment by 5 | No renumbering, easy evolution |
| Manual status checking | CLI + API + dashboards | Automated progress reporting |
| Long build times | Parallel state execution possible | Faster time to delivery |
| Debugging failures | State history with error logs | Faster root cause analysis |

## Migration Strategy

### Phase 1: Pilot (1-2 weeks)
- Deploy API service and database
- Install CLI on build servers
- Instrument one simple pipeline
- Validate state tracking works

### Phase 2: Gradual Adoption (1-2 months)
- Add state tracking to critical pipelines
- Implement artifact storage tracking
- Build dashboards for visibility
- Train teams on CLI usage

### Phase 3: Optimization (Ongoing)
- Implement smart retry logic based on state history
- Optimize parallel state execution
- Add predictive analytics for build time estimation
- Integrate with monitoring/alerting systems

## Technical Architecture

### High-Level Components

```
┌─────────────────────────────────────────────────────────────────┐
│                        Build Pipelines                           │
│  (Concourse, Jenkins, GitHub Actions, GitLab CI, etc.)          │
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │  Packer  │  │ Ansible  │  │  Shell   │  │  Custom  │      │
│  │ Scripts  │  │Playbooks │  │ Scripts  │  │  Tools   │      │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘      │
│       │             │             │             │              │
│       └─────────────┴─────────────┴─────────────┘              │
│                       │                                         │
└───────────────────────┼─────────────────────────────────────────┘
                        │ CLI Commands
                        │ (bldst build add-state, etc.)
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BuildState CLI                                │
│  • Parse commands                                                │
│  • Authenticate with API                                         │
│  • Format input/output                                           │
└───────────────────────┬─────────────────────────────────────────┘
                        │ REST API
                        │ (HTTP/JSON)
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Service                               │
│  • Endpoint routing                                              │
│  • Authentication/Authorization                                  │
│  • Business logic                                                │
│  • State validation                                              │
└───────────────────────┬─────────────────────────────────────────┘
                        │ SQL Queries
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PostgreSQL Database                           │
│  • Build state records                                           │
│  • Build history                                                 │
│  • Artifact locations                                            │
│  • User/API key management                                       │
└─────────────────────────────────────────────────────────────────┘

                        ▲
                        │ Query/Download
                        │
    ┌───────────────────┴───────────────────┐
    │                                       │
┌───▼──────┐  ┌──────────┐  ┌─────────┐   │
│    S3    │  │   NFS    │  │  Ceph   │   │ Artifact Storage
└──────────┘  └──────────┘  └─────────┘   │
```

### Database Schema Highlights

**builds** table:
- Tracks build metadata (project, platform, OS, image type)
- Current state and overall status
- Timestamps for audit trail

**build_states** table:
- Historical record of all state transitions
- State code, status, timestamps
- **Artifact storage tracking fields**:
  - artifact_storage_type (s3, nfs, ebs, ceph, etc.)
  - artifact_storage_path (full URI)
  - artifact_size_bytes
  - artifact_checksum (SHA256/MD5)
  - artifact_metadata (JSON)

**state_codes** table:
- Defines available states per project
- Descriptions, prerequisites, expected durations
- Enables custom state codes per project type

## Conclusion

The State-Based Build Management Framework solves the critical pain points of multi-cloud IaaS image creation:

✅ **Resumable builds** save hours on retries  
✅ **Universal state tracking** provides visibility across all platforms  
✅ **Artifact management** enables distributed build coordination  
✅ **Scalable architecture** adapts to growing complexity  
✅ **Easy integration** with existing tools and pipelines  

By introducing a simple, standardized state code system (0-100) backed by a robust API and database, organizations can:

- **Reduce build time** by 50-80% through intelligent resumption
- **Improve reliability** with clear failure tracking and retry logic
- **Increase visibility** with real-time dashboards and progress reporting
- **Enable coordination** across distributed build infrastructure
- **Simplify maintenance** with a scalable, extensible framework

The framework is designed for **gradual adoption** - start with one pipeline, prove the value, then expand across your organization.

---

**Ready to get started?** See [QUICKSTART.md](../README.md) for installation and deployment instructions.

**Need more details?** See [ARTIFACT-STORAGE.md](ARTIFACT-STORAGE.md) for artifact tracking documentation.

**Last Updated**: February 16, 2026
