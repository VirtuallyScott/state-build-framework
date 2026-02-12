# BuildState CLI

A modern, type-safe command-line interface for the Build State API. Provides a clean alternative to curl commands for pipeline integration and interactive use.

## 🚀 Installation

### From Source (Development)
```bash
git clone <repository-url>
cd buildstate_cli
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
```

### From Wheel (Production)
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Download and install the wheel
pip install buildstate_cli-0.1.0.tar.gz

# Or from private PyPI
pip install --index-url https://your-private-pypi.com/ buildstate_cli
```

### Virtual Environment Best Practices
We strongly recommend using virtual environments to avoid conflicts with system Python packages:

```bash
# Create virtual environment
python -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install the package
pip install buildstate_cli

# Deactivate when done
deactivate
```

## ⚙️ Configuration

### Set API URL
```bash
buildctl config set-url http://localhost:8080
```

### Authentication Options

#### API Key (for Pipelines)
```bash
# Secure storage (recommended)
buildctl auth set-key your-api-key

# Or environment variable
export BUILDCTL_API_KEY=your-api-key
```

#### JWT Token (for Interactive Use)
```bash
# Login interactively
buildctl auth login

# Or set token directly
export BUILDCTL_JWT_TOKEN=your-jwt-token
```

### Configuration File
Create `.buildctl.yaml` in your project root or home directory:

```yaml
api_url: http://localhost:8080
api_key: your-api-key  # Not recommended for production
default_platform: aws-commercial
default_os_version: rhel-8.8
```

## 📋 Usage Examples

### Create a Build
```bash
# Basic build creation
buildctl build create \
  --platform aws-commercial \
  --os rhel-8.8 \
  --type base \
  --id "my-build-$(date +%s)"

# With pipeline context
buildctl build create \
  --platform azure \
  --os ubuntu-22.04 \
  --type hana \
  --id "hana-build-001" \
  --pipeline-url "https://concourse.example.com/pipelines/hana" \
  --commit "abc123def"
```

### Update Build State
```bash
# State progression (0 → 10 → 25 → 50 → 75 → 100)
buildctl state update <build-uuid> --state 10 --message "Starting preparation"
buildctl state update <build-uuid> --state 25 --message "Packer validation complete"
buildctl state update <build-uuid> --state 50 --message "Ansible configuration running"
buildctl state update <build-uuid> --state 100 --message "Build completed successfully"
```

### Record Failures
```bash
# Record build failure
buildctl failure record <build-uuid> \
  --error "Packer build failed: AMI creation timeout" \
  --code "PACKER_TIMEOUT" \
  --component "packer"
```

### Query Builds
```bash
# Get build details
buildctl build get <build-uuid>

# List builds by platform
buildctl build list --platform aws-commercial --limit 20

# Get current state
buildctl state get <build-uuid>
```

### Dashboard
```bash
# View summary
buildctl dashboard summary

# View recent builds
buildctl dashboard recent --limit 15
```

## 🔧 Concourse Pipeline Integration

### Example Pipeline Task
```yaml
jobs:
- name: build-image
  plan:
  - task: init-build
    config:
      platform: linux
      image_resource:
        type: registry-image
        source:
          repository: your-registry/buildstate_cli
          tag: latest
      run:
        path: sh
        args:
        - -c
        - |
          # Install CLI if not in image
          pip install buildstate_cli

          # Configure API access
          export BUILDCTL_API_URL=http://build-api.example.com
          export BUILDCTL_API_KEY=${API_KEY}

          # Create build
          BUILD_UUID=$(buildctl build create \
            --platform aws \
            --os rhel-8.8 \
            --type base \
            --id "build-${BUILD_ID}" \
            --pipeline-url "${ATC_EXTERNAL_URL}/pipelines/${PIPELINE_NAME}")

          echo $BUILD_UUID > build-uuid.txt

  - task: packer-build
    config:
      run:
        path: sh
        args:
        - -c
        - |
          BUILD_UUID=$(cat build-uuid.txt)

          # Update state
          buildctl state update $BUILD_UUID \
            --state 10 \
            --message "Starting Packer build"

          # Run packer
          packer build -var-file=vars.json template.json

          # Update on success
          buildctl state update $BUILD_UUID \
            --state 25 \
            --message "Packer build completed"

  - task: ansible-configure
    config:
      run:
        path: sh
        args:
        - -c
        - |
          BUILD_UUID=$(cat build-uuid.txt)

          buildctl state update $BUILD_UUID \
            --state 50 \
            --message "Starting Ansible configuration"

          ansible-playbook playbook.yml

          buildctl state update $BUILD_UUID \
            --state 75 \
            --message "Ansible configuration completed"

  - task: finalize
    config:
      run:
        path: sh
        args:
        - -c
        - |
          BUILD_UUID=$(cat build-uuid.txt)

          buildctl state update $BUILD_UUID \
            --state 100 \
            --message "Build completed successfully"

  on_failure:
    do:
    - task: record-failure
      config:
        run:
          path: sh
          args:
        - -c
        - |
          BUILD_UUID=$(cat build-uuid.txt)
          buildctl failure record $BUILD_UUID \
            --error "Pipeline failed at stage: ${FAILED_JOB}" \
            --code "PIPELINE_FAILURE" \
            --component "concourse"
```

## 🎯 Key Advantages over Curl

### Type Safety & Validation
```bash
# CLI validates input before API call
buildctl state update <uuid> --state 23
❌ Error: State code must be a multiple of 5 (got 23)

# Curl would send invalid data to API
curl -X POST /builds/<uuid>/state -d '{"state_code": 23}'
```

### Better Error Messages
```bash
# CLI provides clear, actionable errors
❌ curl: (22) The requested URL returned error: 400
✅ Error: Invalid state code '23'. State codes must be multiples of 5 (0, 5, 10, ..., 100)
```

### Auto-completion & Help
```bash
buildctl --help                    # Show all commands
buildctl build create --help       # Command-specific help
buildctl state update --help       # Parameter details
buildctl <TAB><TAB>               # Auto-complete commands
```

### Configuration Management
```bash
# One-time setup, works everywhere
buildctl config set-url http://api.example.com
buildctl auth set-key my-key

# No need to remember URLs/keys in every pipeline
```

### Rich Output Formatting
```bash
# Beautiful tables and status indicators
buildctl dashboard summary
# 📊 Build State Dashboard
# Total Builds: 42
# ┌─────────────┬───────┐
# │ Status      │ Count │
# ├─────────────┼───────┤
# │ Completed   │ 38    │
# │ Failed      │ 2     │
# │ In Progress │ 2     │
# └─────────────┴───────┘
```

## 🏗️ Architecture

### Shared Models
- **Type-safe**: Pydantic models shared between CLI and API
- **Validation**: Input validation before API calls
- **Consistency**: Same models ensure compatibility

### Async HTTP Client
- **httpx**: Modern async HTTP client
- **Error Handling**: Rich error messages and status codes
- **Authentication**: Automatic JWT/API key handling

### Configuration System
- **Multiple Sources**: Environment variables, config files, keyring
- **Security**: API keys stored securely via keyring
- **Flexibility**: Per-project or global configuration

### CLI Framework
- **Typer**: Modern CLI framework with auto-completion
- **Rich**: Beautiful terminal output and formatting
- **Async Support**: Non-blocking API calls

## 🔒 Security

### API Key Storage
```bash
# Secure storage using system keyring
buildctl auth set-key your-api-key

# Keys stored securely, not in config files
```

### Environment Variables
```bash
# For CI/CD systems
export BUILDCTL_API_URL=https://api.example.com
export BUILDCTL_API_KEY=your-key
```

### JWT Tokens
```bash
# Interactive login with secure token storage
buildctl auth login
# Tokens automatically refreshed
```

## 🚀 Development

### Setup Development Environment
```bash
# Clone and install in development mode
git clone <repository-url>
cd buildstate_cli
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black .
isort .

# Type checking
mypy buildstate
```

### Building Distribution
```bash
# Build wheel
python -m build

# Install locally for testing
pip install dist/buildstate_cli-0.1.0.tar.gz

# Test CLI
buildctl --help
```

## 📚 API Reference

### Commands

- `buildctl config` - Manage configuration
- `buildctl auth` - Manage authentication
- `buildctl build` - Build operations
- `buildctl state` - State management
- `buildctl failure` - Failure recording
- `buildctl dashboard` - View summaries
- `buildctl health` - Health checks

### Global Options
- `--verbose, -v` - Enable verbose output
- `--config` - Specify config file path

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Run `black . && isort . && mypy buildstate`
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

---

**Clean pipelines, happy engineers! 🎉**