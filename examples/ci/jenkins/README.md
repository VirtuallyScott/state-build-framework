# Jenkins CI/CD Examples for Build State API

This directory contains example Jenkins pipelines and a shared library for integrating the Build State API (`bldst` CLI) into your CI/CD workflows.

## Directory Structure

```
jenkins/
├── README.md                           # This file
├── pipelines/                          # Example Jenkinsfiles
│   ├── simple-build.jenkinsfile        # Basic build state tracking
│   ├── image-build-with-artifacts.jenkinsfile  # Image build with artifact tracking
│   ├── resumable-build.jenkinsfile     # Resumable build workflow
│   └── multi-stage-pipeline.jenkinsfile # Complex multi-stage example
└── shared-library/                     # Jenkins Shared Library
    ├── vars/                           # Global variables and functions
    │   ├── buildState.groovy           # Main build state wrapper
    │   └── bldstCLI.groovy             # CLI installation and management
    └── src/                            # Groovy classes (if needed)
```

## Quick Start

### 1. Install the Shared Library

Add this shared library to your Jenkins instance:

**Jenkins Configuration > Global Pipeline Libraries:**

- **Name:** `buildstate-lib`
- **Default version:** `main` (or specific tag/branch)
- **Retrieval method:** Modern SCM
- **Source Code Management:** Git
- **Project Repository:** `https://github.com/your-org/state-builds.git`
- **Library Path:** `examples/ci/jenkins/shared-library`

### 2. Use in Your Jenkinsfile

```groovy
@Library('buildstate-lib') _

pipeline {
    agent any
    
    environment {
        BUILDSTATE_API_URL = 'https://buildstate-api.example.com'
        BUILDSTATE_API_KEY = credentials('buildstate-api-key')
        PROJECT_ID = 'my-project-id'
    }
    
    stages {
        stage('Start Build') {
            steps {
                script {
                    buildState.start(
                        project: env.PROJECT_ID,
                        name: "Build-${env.BUILD_NUMBER}",
                        platform: 'aws',
                        osVersion: 'ubuntu-22.04'
                    )
                }
            }
        }
        
        stage('Build Image') {
            steps {
                script {
                    buildState.updateState(100, 'Building base image')
                    // Your build steps here
                }
            }
        }
        
        stage('Complete') {
            steps {
                script {
                    buildState.complete()
                }
            }
        }
    }
    
    post {
        failure {
            script {
                buildState.fail('Build failed')
            }
        }
    }
}
```

## Shared Library Features

The `buildstate-lib` shared library provides:

### Automatic CLI Management
- **Auto-installation:** Automatically installs the latest `bldst` CLI version
- **Version pinning:** Pin to specific versions for stability
- **Virtual environment:** Isolated Python environment per build
- **Cache support:** Reuses CLI installation across builds when possible

### Simple API Wrappers
- `buildState.start()` - Initialize a new build
- `buildState.updateState()` - Update build state with progress
- `buildState.recordArtifact()` - Register build artifacts
- `buildState.setVariable()` - Store build variables for resumption
- `buildState.complete()` - Mark build as successful
- `buildState.fail()` - Mark build as failed
- `buildState.resume()` - Resume a failed build from a checkpoint

### Configuration Options

Environment variables for customization:

| Variable | Description | Default |
|----------|-------------|---------|
| `BUILDSTATE_API_URL` | Build State API endpoint | Required |
| `BUILDSTATE_API_KEY` | API authentication key | Required |
| `BUILDSTATE_CLI_VERSION` | Specific CLI version to use | `latest` |
| `BUILDSTATE_DEBUG` | Enable debug logging | `false` |
| `BUILDSTATE_TIMEOUT` | API request timeout (seconds) | `30` |

## Example Pipelines

### Simple Build Tracking
[`pipelines/simple-build.jenkinsfile`](pipelines/simple-build.jenkinsfile)

Basic example showing state tracking through a simple build process.

### Image Build with Artifacts
[`pipelines/image-build-with-artifacts.jenkinsfile`](pipelines/image-build-with-artifacts.jenkinsfile)

Demonstrates artifact tracking for VM snapshots, disk images, and AMIs.

### Resumable Build Workflow
[`pipelines/resumable-build.jenkinsfile`](pipelines/resumable-build.jenkinsfile)

Shows how to implement resumable builds with checkpoint/resume capabilities.

### Multi-Stage Pipeline
[`pipelines/multi-stage-pipeline.jenkinsfile`](pipelines/multi-stage-pipeline.jenkinsfile)

Complex example with multiple platforms, parallel stages, and comprehensive state tracking.

## Best Practices

### 1. Use Credentials for API Keys
Always store API keys in Jenkins credentials:

```groovy
environment {
    BUILDSTATE_API_KEY = credentials('buildstate-api-key')
}
```

### 2. Handle Build Failures
Always use `post` blocks to record failures:

```groovy
post {
    failure {
        script {
            buildState.fail("Build failed: ${currentBuild.result}")
        }
    }
}
```

### 3. Track Artifacts Early
Register artifacts as soon as they're created:

```groovy
buildState.recordArtifact(
    type: 'vm-snapshot',
    location: "snapshots/${snapshotId}",
    isResumable: true
)
```

### 4. Use Variables for Resume Context
Store critical state information:

```groovy
buildState.setVariable('vm_id', vmId, required: true)
buildState.setVariable('network_config', networkJson, required: true)
```

### 5. Pin CLI Versions for Production
Use specific versions in production pipelines:

```groovy
environment {
    BUILDSTATE_CLI_VERSION = '1.2.3'
}
```

## Troubleshooting

### CLI Installation Issues
If the CLI fails to install, check:
- Python 3.8+ is available on the agent
- Network access to PyPI
- Write permissions in the workspace

### API Connection Issues
If unable to connect to the API:
- Verify `BUILDSTATE_API_URL` is correct
- Check API key is valid and not expired
- Ensure network connectivity from Jenkins agents
- Review API server logs

### Build State Not Updating
If states aren't being recorded:
- Enable debug mode: `BUILDSTATE_DEBUG=true`
- Check Jenkins console output for CLI errors
- Verify the build ID is being properly stored

## Support

For issues or questions:
- API Documentation: [API Reference](../../api_service/docs/API-REFERENCE.md)
- CLI Documentation: [CLI Reference](../../bldst_cli/README.md)
- Architecture: [System Architecture](../../api_service/docs/ARCHITECTURE.md)

## Contributing

To add new examples or improve the shared library:
1. Create examples that demonstrate real-world use cases
2. Document all configuration options
3. Include error handling and retry logic
4. Test with multiple Jenkins versions
5. Submit a pull request with clear descriptions
