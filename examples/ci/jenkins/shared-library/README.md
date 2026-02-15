# Build State Shared Library

Jenkins Shared Library for seamless integration with the Build State API.

## Overview

This shared library provides a standardized way to interact with the Build State API from Jenkins pipelines. It handles:

- **Automatic CLI Installation**: Installs and manages the `bldst` CLI tool
- **Version Management**: Supports version pinning and automatic updates
- **Simple API**: High-level wrapper functions for common operations
- **Error Handling**: Robust error handling and retry logic
- **Isolation**: Uses Python virtual environments per build

## Installation

### Option 1: Global Shared Library (Recommended)

Configure as a global shared library in Jenkins:

1. Go to **Manage Jenkins > Configure System**
2. Scroll to **Global Pipeline Libraries**
3. Click **Add** and configure:

```
Name: buildstate-lib
Default version: main
Retrieval method: Modern SCM
  Source Code Management: Git
  Project Repository: https://github.com/your-org/state-builds.git
Library Path: examples/ci/jenkins/shared-library
```

4. Optionally check **Load implicitly** to make it available to all pipelines
5. Click **Save**

### Option 2: Per-Pipeline Library

Add to individual Jenkinsfiles:

```groovy
library(
    identifier: 'buildstate-lib@main',
    retriever: modernSCM([
        $class: 'GitSCMSource',
        remote: 'https://github.com/your-org/state-builds.git',
        credentialsId: 'github-credentials'
    ])
)
```

### Option 3: Local Repository

For development and testing:

```groovy
library(
    identifier: 'buildstate-lib@main',
    retriever: legacySCM([
        $class: 'GitSCM',
        branches: [[name: 'main']],
        userRemoteConfigs: [[url: '/path/to/state-builds.git']]
    ])
)
```

## Quick Start

### 1. Import the Library

At the top of your Jenkinsfile:

```groovy
@Library('buildstate-lib') _
```

### 2. Configure Environment Variables

```groovy
environment {
    BUILDSTATE_API_URL = 'https://buildstate-api.example.com'
    BUILDSTATE_API_KEY = credentials('buildstate-api-key')
}
```

### 3. Use in Your Pipeline

```groovy
pipeline {
    stages {
        stage('Start Build') {
            steps {
                script {
                    buildState.start(
                        project: 'project-uuid',
                        name: "Build-${BUILD_NUMBER}",
                        platform: 'aws'
                    )
                }
            }
        }
        
        stage('Build') {
            steps {
                script {
                    buildState.updateState(100, 'Building...')
                    // Your build steps
                }
            }
        }
    }
}
```

## Library Components

### bldstCLI - CLI Management

Low-level CLI installation and execution.

#### Functions

**`install(version, force)`**
```groovy
bldstCLI.install('1.2.3')  // Install specific version
bldstCLI.install('latest') // Install latest version
bldstCLI.install('latest', true) // Force reinstall
```

**`exec(command, args, returnOutput)`**
```groovy
// Execute and return output
def output = bldstCLI.exec('build list', [project_id: 'xxx'], true)

// Execute for status code only
def status = bldstCLI.exec('build create', [name: 'test'], false)
```

**`verifyConnection()`**
```groovy
if (bldstCLI.verifyConnection()) {
    echo "API connection OK"
}
```

**`getVersion()`**
```groovy
def version = bldstCLI.getVersion()
echo "CLI version: ${version}"
```

**`cleanup()`**
```groovy
bldstCLI.cleanup()  // Remove CLI installation
```

---

### buildState - High-Level API

High-level wrapper for build state operations.

#### Functions

**`start(config)`** - Start a new build
```groovy
buildState.start(
    project: 'project-uuid',          // Required
    name: 'My Build',                 // Optional: defaults to job name
    platform: 'aws',                  // Optional
    osVersion: 'ubuntu-22.04',        // Optional
    imageType: 'base-image',          // Optional
    startState: 0,                    // Optional: default 0
    metadata: [key: 'value']          // Optional
)
```

**`updateState(stateCode, message, metadata)`** - Update build state
```groovy
buildState.updateState(100, 'Starting build')
buildState.updateState(200, 'Compiling', [compiler: 'gcc'])
```

**`recordArtifact(config)`** - Record a build artifact
```groovy
buildState.recordArtifact(
    type: 'vm-snapshot',                    // Required
    location: 'snapshot:snap-12345',        // Required
    stateCode: 300,                         // Optional
    isResumable: true,                      // Optional
    isFinal: false,                         // Optional
    checksumType: 'sha256',                 // Optional
    checksumValue: 'abc123...',             // Optional
    sizeBytes: 1073741824,                  // Optional
    metadata: [region: 'us-east-1']         // Optional
)
```

**`setVariable(key, value, config)`** - Set a build variable
```groovy
// Simple variable
buildState.setVariable('vm_id', 'i-1234567890')

// With configuration
buildState.setVariable('api_key', 'secret', [
    sensitive: true,
    required: true,
    stateCode: 100
])
```

**`getVariable(key)`** - Get a build variable
```groovy
def vmId = buildState.getVariable('vm_id')
```

**`complete(message, finalState)`** - Mark build as complete
```groovy
buildState.complete('Build successful', 999)
```

**`fail(message, errorCode)`** - Mark build as failed
```groovy
buildState.fail('Build failed: compilation error', -1)
```

**`resume(buildId, resumeFromState)`** - Resume a previous build
```groovy
def context = buildState.resume('build-uuid', 500)
```

**`getBuildDetails(buildId)`** - Get build details
```groovy
def details = buildState.getBuildDetails('build-uuid')
```

**`listArtifacts()`** - List all artifacts for current build
```groovy
def artifacts = buildState.listArtifacts()
```

## Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `BUILDSTATE_API_URL` | Build State API endpoint | Yes | - |
| `BUILDSTATE_API_KEY` | API authentication key | Yes | - |
| `BUILDSTATE_CLI_VERSION` | Specific CLI version to use | No | `latest` |
| `BUILDSTATE_DEBUG` | Enable debug logging | No | `false` |
| `BUILDSTATE_TIMEOUT` | API request timeout (seconds) | No | `30` |

### Example Configuration

```groovy
environment {
    // Required
    BUILDSTATE_API_URL = 'https://buildstate-api.example.com'
    BUILDSTATE_API_KEY = credentials('buildstate-api-key')
    
    // Optional
    BUILDSTATE_CLI_VERSION = '1.2.3'
    BUILDSTATE_DEBUG = 'true'
    BUILDSTATE_TIMEOUT = '60'
}
```

## Best Practices

### 1. Use Jenkins Credentials

Always store API keys in Jenkins credentials:

```groovy
environment {
    BUILDSTATE_API_KEY = credentials('buildstate-api-key')
}
```

### 2. Handle Failures in post Blocks

```groovy
post {
    failure {
        script {
            buildState.fail("Build failed: ${currentBuild.result}")
        }
    }
}
```

### 3. Store Critical Variables for Resume

```groovy
buildState.setVariable('vm_id', vmId, [required: true])
buildState.setVariable('network_id', netId, [required: true])
```

### 4. Mark Resumable Artifacts

```groovy
buildState.recordArtifact(
    type: 'vm-snapshot',
    location: snapshotId,
    isResumable: true,  // Enables resume from this point
    isFinal: false
)
```

### 5. Pin CLI Versions in Production

```groovy
environment {
    BUILDSTATE_CLI_VERSION = '1.2.3'  // Pin to stable version
}
```

### 6. Use Descriptive Build Names

```groovy
buildState.start(
    project: PROJECT_ID,
    name: "${env.OS_VERSION}-${env.PLATFORM}-${env.BUILD_NUMBER}"
)
```

### 7. Add Metadata for Context

```groovy
buildState.start(
    project: PROJECT_ID,
    metadata: [
        jenkins_job: env.JOB_NAME,
        git_commit: env.GIT_COMMIT,
        triggered_by: env.BUILD_CAUSE
    ]
)
```

## Troubleshooting

### CLI Installation Fails

**Symptom:** Error during `bldstCLI.install()`

**Solutions:**
- Verify Python 3.8+ is available: `python3 --version`
- Check network access to PyPI
- Verify write permissions in workspace
- Try force reinstall: `bldstCLI.install('latest', true)`

### API Connection Issues

**Symptom:** Cannot connect to Build State API

**Solutions:**
- Verify `BUILDSTATE_API_URL` is correct
- Check API key is valid: test with curl
- Ensure network connectivity from Jenkins agent
- Enable debug mode: `BUILDSTATE_DEBUG=true`
- Check API server logs

### Build ID Not Found

**Symptom:** "No active build" errors

**Solution:**
- Ensure `buildState.start()` was called
- Check `env.BUILDSTATE_BUILD_ID` is set
- Verify stages run after initialization

### Virtual Environment Conflicts

**Symptom:** Python package conflicts

**Solutions:**
- Clean up venv: `bldstCLI.cleanup()`
- Force reinstall CLI
- Check for multiple Python versions

## Development

### Testing Locally

Test the shared library locally before deployment:

```bash
# Clone the repository
git clone https://github.com/your-org/state-builds.git
cd state-builds/examples/ci/jenkins/shared-library

# Create a test Jenkinsfile
# Use library() to reference local path

# Run with Jenkins Pipeline Unit Testing
./gradlew test
```

### Adding New Functions

1. Add function to appropriate file in `vars/`
2. Document with JavaDoc-style comments
3. Add example to README
4. Test with sample pipelines
5. Submit pull request

### Versioning

Use Git tags for versions:

```bash
git tag -a v1.2.3 -m "Release 1.2.3"
git push origin v1.2.3
```

Reference specific versions in Jenkinsfile:

```groovy
@Library('buildstate-lib@v1.2.3') _
```

## Contributing

Contributions welcome! Please:

1. Follow existing code style
2. Add comprehensive documentation
3. Include usage examples
4. Test with multiple Jenkins versions
5. Update CHANGELOG.md

## License

See main repository LICENSE file.

## Support

- **Documentation**: [Main README](../README.md)
- **API Reference**: [API Docs](../../../api_service/docs/API_REFERENCE.md)
- **Issues**: GitHub Issues
- **Questions**: Discussions or Slack channel
