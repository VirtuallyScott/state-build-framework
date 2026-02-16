# Concourse CI Examples for Build State API

This directory contains example Concourse pipelines and tasks for integrating the Build State API (`bldst` CLI) into your image build workflows.

## Directory Structure

```
concourse/
├── README.md                        # This file
├── pipelines/                       # Example pipeline YAML files
│   ├── simple-image-build.yml       # Basic image build with state tracking
│   ├── multi-platform-build.yml     # Build images for multiple platforms
│   └── resumable-build.yml          # Resumable build with checkpoints
└── tasks/                           # Reusable task definitions
    ├── bldst-init.yml               # Initialize build state tracking
    ├── bldst-update-state.yml       # Update build state
    ├── bldst-record-artifact.yml    # Record build artifacts
    └── bldst-complete.yml           # Mark build as complete/failed
```

## Prerequisites

### 1. Build State API
Ensure you have the Build State API deployed and accessible from your Concourse workers.

### 2. Credentials
Store API credentials in Concourse:

```bash
# Using fly CLI
fly -t <target> set-pipeline \
  -p my-build \
  -c pipelines/simple-image-build.yml \
  -v buildstate-api-url=https://api.example.com \
  -v buildstate-api-key=((buildstate-api-key))
```

Or use credential manager (Vault, CredHub, etc.):

```yaml
# In your pipeline
- name: build-image
  params:
    BLDST_API_URL: ((buildstate.api_url))
    BLDST_API_KEY: ((buildstate.api_key))
```

### 3. Docker Image with bldst CLI

#### Option A: Use our pre-built image
```yaml
image_resource:
  type: registry-image
  source:
    repository: your-registry/buildstate-cli
    tag: latest
```

#### Option B: Build your own
```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Install bldst CLI
RUN pip install --no-cache-dir buildstate-cli

# Verify installation
RUN bldst --version

WORKDIR /workspace
```

Build and push:
```bash
docker build -t your-registry/buildstate-cli:latest .
docker push your-registry/buildstate-cli:latest
```

## Quick Start

### 1. Deploy a Simple Pipeline

```bash
fly -t production set-pipeline \
  -p rhel-image-build \
  -c pipelines/simple-image-build.yml \
  -v buildstate-api-url=https://buildstate.example.com \
  -v project-id=<your-project-uuid>
```

### 2. Trigger the Pipeline

```bash
fly -t production trigger-job -j rhel-image-build/build-image
```

### 3. Watch the Build

```bash
fly -t production watch -j rhel-image-build/build-image
```

## Pipeline Examples

### Simple Image Build
[`pipelines/simple-image-build.yml`](pipelines/simple-image-build.yml)

Basic example showing:
- Build state initialization
- State updates through build phases
- Artifact registration
- Error handling

### Multi-Platform Build
[`pipelines/multi-platform-build.yml`](pipelines/multi-platform-build.yml)

Advanced example with:
- Parallel builds for multiple platforms (AWS, Azure, GCP)
- Reference data lookups
- Fan-out/fan-in pattern
- Consolidated reporting

### Resumable Build
[`pipelines/resumable-build.yml`](pipelines/resumable-build.yml)

Demonstrates:
- Checkpoint creation at key stages
- Artifact and variable registration
- Resume from failure points
- State recovery

## Task Library

Reusable tasks for common operations:

### Initialize Build State
[`tasks/bldst-init.yml`](tasks/bldst-init.yml)

Initialize a new build record and store the build UUID.

**Usage:**
```yaml
- task: init-build-state
  file: tasks/bldst-init.yml
  params:
    BLDST_API_URL: ((buildstate-api-url))
    BLDST_API_KEY: ((buildstate-api-key))
    PROJECT_ID: ((project-id))
    BUILD_NAME: rhel-8-base
```

### Update Build State
[`tasks/bldst-update-state.yml`](tasks/bldst-update-state.yml)

Update the build state at various checkpoints.

**Usage:**
```yaml
- task: update-state
  file: tasks/bldst-update-state.yml
  params:
    STATE_CODE: "25"
    STATE_MESSAGE: "Packer build completed"
```

### Record Artifact
[`tasks/bldst-record-artifact.yml`](tasks/bldst-record-artifact.yml)

Register build artifacts for tracking and resumption.

**Usage:**
```yaml
- task: record-artifact
  file: tasks/bldst-record-artifact.yml
  params:
    ARTIFACT_TYPE: ami
    ARTIFACT_ID: ami-1234567890abcdef0
```

### Complete Build
[`tasks/bldst-complete.yml`](tasks/bldst-complete.yml)

Mark build as successfully completed or failed.

**Usage:**
```yaml
- task: complete-build
  file: tasks/bldst-complete.yml
  params:
    SUCCESS: "true"
```

## Best Practices

### 1. Store Build UUID in Output
Always save the build UUID for use in subsequent tasks:

```yaml
outputs:
  - name: build-info
    
run:
  path: sh
  args:
    - -c
    - |
      BUILD_UUID=$(bldst build create ...)
      echo $BUILD_UUID > build-info/uuid.txt
```

### 2. Use Passed Constraints
Ensure tasks run in sequence by using `passed`:

```yaml
- get: build-info
  passed: [init-build]
```

### 3. Handle Failures
Always use `on_failure` to record build failures:

```yaml
on_failure:
  task: record-failure
  file: tasks/bldst-complete.yml
  params:
    SUCCESS: "false"
    FAILURE_MESSAGE: "Packer build failed"
```

### 4. Use Environment Variables
Store API configuration in secrets:

```yaml
params:
  BLDST_API_URL: ((buildstate.api_url))
  BLDST_API_KEY: ((buildstate.api_key))
```

### 5. Enable Debug Output (Development Only)
For troubleshooting, enable debug mode:

```yaml
params:
  BLDST_DEBUG: "true"
```

## Integration with Packer

See [`../../packer/templates/`](../../packer/templates/) for complete Packer templates that integrate with these pipelines.

Example workflow:
1. Initialize build state (Concourse task)
2. Run Packer build (calls bldst CLI from provisioners)
3. Record artifacts (Concourse task)
4. Complete build state (Concourse task)

## Troubleshooting

### CLI Installation Issues
If the CLI fails to install:
```yaml
# Add to your task
run:
  path: sh
  args:
    - -c
    - |
      python3 --version
      pip3 install --upgrade pip
      pip3 install buildstate-cli
      bldst --version
```

### API Connection Issues
Verify connectivity:
```yaml
run:
  path: sh
  args:
    - -c
    - |
      bldst config set-url $BLDST_API_URL
      bldst auth set-key $BLDST_API_KEY
      bldst health check
```

### Build UUID Not Found
Ensure the build UUID is passed between tasks:
```yaml
# In producing task
outputs:
  - name: build-info

# In consuming task
inputs:
  - name: build-info

run:
  path: sh
  args:
    - -c
    - |
      BUILD_UUID=$(cat build-info/uuid.txt)
      bldst build get $BUILD_UUID
```

## Resources

- **API Documentation**: [API Reference](../../../api_service/docs/API_REFERENCE.md)
- **CLI Documentation**: [CLI Guide](../../../buildstate_cli/README.md)
- **Architecture**: [System Architecture](../../../api_service/docs/ARCHITECTURE.md)
- **Packer Examples**: [Packer Templates](../../packer/)

## Contributing

To contribute new examples:
1. Follow existing naming conventions
2. Add comprehensive comments
3. Include error handling
4. Test with actual Concourse deployment
5. Update this README
6. Submit a pull request
