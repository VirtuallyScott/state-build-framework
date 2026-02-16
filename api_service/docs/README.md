# Build State API Service

A scalable, containerized FastAPI service for managing multi-cloud IaaS image build states with JWT and API key authentication.

## Architecture

- **Horizontal Scaling**: Multiple API containers behind Nginx load balancer
- **Authentication**: JWT tokens and API keys
- **Database**: SQLite (default) or PostgreSQL
- **Caching**: Redis for dashboard caching and session management
- **Containerization**: Multi-stage Docker builds
- **Load Balancing**: Nginx with least-connections algorithm

## Features

- ✅ JWT and API key authentication
- ✅ RESTful API for build state management
- ✅ Horizontal scaling with multiple containers
- ✅ Nginx reverse proxy with load balancing
- ✅ Redis caching for performance
- ✅ Health checks and monitoring
- ✅ SQLite/PostgreSQL support
- ✅ Multi-stage Docker builds
- ✅ Comprehensive error handling

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Git

### 1. Clone and Setup

```bash
cd /path/to/your/project
git clone <repository-url> api_service
cd api_service

# Copy environment template
cp .env.example .env

# Edit environment variables
nano .env
```

### 2. Build and Run

```bash
# Build and start all services
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

### 3. Verify Deployment

```bash
# Check if services are running
docker-compose ps

# Test API health
curl http://localhost:8080/

# Get API documentation
open http://localhost:8080/docs
```

## API Usage

### Authentication

We provide the `bldst` CLI tool which eliminates the need for complex curl commands. The CLI handles authentication, formatting, and error handling automatically.

#### Install the CLI
```bash
cd buildstate_cli
pip install -e .
```

#### Configure API Access
```bash
# Set the API URL
bldst config set-url http://localhost:8080

# Set API Key (recommended for automation)
bldst auth set-key your-api-key

# Or login with username/password (for interactive use)
bldst auth login
```

#### Verify Configuration
```bash
bldst config show
bldst health check
```

### Core Endpoints

**Note:** All examples below use the `bldst` CLI. For direct API access, see the [API Reference](API_REFERENCE.md).

#### Create Build
```bash
# Create a new build (returns UUID for tracking)
bldst build create \
  --build-number "my-build-001" \
  --project-id <project-uuid> \
  --platform-id <platform-uuid> \
  --os-version-id <os-version-uuid> \
  --image-type-id <image-type-uuid> \
  --created-by "jenkins-pipeline" \
  --concourse-url "https://concourse.example.com/pipelines/my-pipeline"

# To get UUIDs for reference data:
bldst platform list
bldst os-version list
bldst image-type list
bldst project list
```

#### Update Build State
```bash
# Add a new state to a build (state progression: 0 → 10 → 25 → 50 → 75 → 100)
bldst build add-state <build-uuid> \
  --state 25 \
  --status "Packer build completed successfully"

# Example state progression:
bldst build add-state <build-uuid> --state 10 --status "Starting preparation"
bldst build add-state <build-uuid> --state 25 --status "Packer validation complete"
bldst build add-state <build-uuid> --state 50 --status "Ansible configuration running"
bldst build add-state <build-uuid> --state 100 --status "Build completed successfully"
```

#### Record Failure
```bash
# Record a build failure with details
bldst build add-failure <build-uuid> \
  --state 25 \
  --type "PACKER_TIMEOUT" \
  --message "Packer build failed: AMI creation timeout after 3600 seconds"
```

#### Get Build Details
```bash
# Get complete build information
bldst build get <build-uuid>

# List recent builds
bldst build list --limit 20
```

#### Dashboard & Monitoring
```bash
# View comprehensive dashboard summary
bldst dashboard summary

# View recent builds
bldst dashboard recent

# Health check
bldst health check
```

### Health and Status Endpoints

#### Health Check (CLI)
```bash
# Quick health check
bldst health check

# Check API readiness (verifies database and Redis connectivity)
bldst health ready

# Get comprehensive status of all components
bldst health status
```

#### Health Check (Direct API)
For monitoring systems that need direct HTTP access:
```bash
# Basic health
curl http://localhost:8080/health

# Readiness check (database + Redis)
curl http://localhost:8080/ready

# Full status (all components)
curl http://localhost:8080/status

# Status server (requires /etc/hosts: 127.0.0.1 status.localbuild.api)
curl http://status.localbuild.api/
```

## Concourse Pipeline Integration

The `bldst` CLI provides a much cleaner, more maintainable approach for CI/CD pipelines compared to curl commands.

### Key Benefits
- ✅ **No more brittle curl commands** - Clean, readable syntax
- ✅ **Built-in error handling** - Automatic retry logic and clear error messages
- ✅ **Automatic authentication** - Set once, use everywhere
- ✅ **Type safety** - Validates input before sending to API
- ✅ **Output parsing** - Structured JSON output for pipeline consumption

### Prerequisites

Create a Docker image with the CLI pre-installed:

```dockerfile
FROM python:3.11-slim

# Install bldst CLI
RUN pip install buildstate-cli

# Or install from source
# COPY buildstate_cli /tmp/buildstate_cli
# RUN cd /tmp/buildstate_cli && pip install -e .

WORKDIR /workspace
```

### Example Pipeline Task

```yaml
jobs:
- name: build-rhel-image
  plan:
  - task: create-build-record
    config:
      platform: linux
      image_resource:
        type: registry-image
        source:
          repository: your-registry/buildstate-cli
          tag: latest
      params:
        BLDST_API_URL: http://build-api.example.com
        BLDST_API_KEY: ((buildstate-api-key))  # From Concourse secrets
      outputs:
        - name: build-info
      run:
        path: sh
        args:
          - -c
          - |
            set -e
            
            # Configure CLI (one time)
            bldst config set-url ${BLDST_API_URL}
            bldst auth set-key ${BLDST_API_KEY}
            
            # Get reference data UUIDs (cache these in your pipeline if needed)
            PLATFORM_ID=$(bldst platform list --output json | jq -r '.[] | select(.name=="aws-commercial") | .id')
            OS_VERSION_ID=$(bldst os-version list --output json | jq -r '.[] | select(.version=="rhel-8.8") | .id')
            IMAGE_TYPE_ID=$(bldst image-type list --output json | jq -r '.[] | select(.name=="base") | .id')
            PROJECT_ID=$(bldst project list --output json | jq -r '.[] | select(.name=="platform-images") | .id')
            
            # Create build record
            BUILD_UUID=$(bldst build create \
              --build-number "build-${BUILD_ID}" \
              --project-id ${PROJECT_ID} \
              --platform-id ${PLATFORM_ID} \
              --os-version-id ${OS_VERSION_ID} \
              --image-type-id ${IMAGE_TYPE_ID} \
              --created-by "concourse-${BUILD_PIPELINE_NAME}" \
              --concourse-url "${ATC_EXTERNAL_URL}/teams/${BUILD_TEAM_NAME}/pipelines/${BUILD_PIPELINE_NAME}" \
              --output json | jq -r '.id')
            
            echo ${BUILD_UUID} > build-info/uuid.txt
            echo "✅ Build record created: ${BUILD_UUID}"

  - task: update-state-preparing
    config:
      platform: linux
      image_resource:
        type: registry-image
        source:
          repository: your-registry/buildstate-cli
          tag: latest
      params:
        BLDST_API_URL: http://build-api.example.com
        BLDST_API_KEY: ((buildstate-api-key))
      inputs:
        - name: build-info
      run:
        path: sh
        args:
          - -c
          - |
            set -e
            bldst config set-url ${BLDST_API_URL}
            bldst auth set-key ${BLDST_API_KEY}
            
            BUILD_UUID=$(cat build-info/uuid.txt)
            bldst build add-state ${BUILD_UUID} --state 10 --status "Preparing build environment"

  - task: packer-build
    config:
      platform: linux
      inputs:
        - name: build-info
        - name: packer-templates
      outputs:
        - name: build-artifacts
      run:
        path: sh
        args:
          - -c
          - |
            set -e
            
            # Update state before starting
            BUILD_UUID=$(cat build-info/uuid.txt)
            bldst build add-state ${BUILD_UUID} --state 25 --status "Running Packer build"
            
            # Run packer
            packer build -var-file=vars.json packer-templates/template.json
            
            # Update state on success
            bldst build add-state ${BUILD_UUID} --state 50 --status "Packer build completed"
    on_failure:
      task: record-packer-failure
      config:
        platform: linux
        inputs:
          - name: build-info
        run:
          path: sh
          args:
            - -c
            - |
              BUILD_UUID=$(cat build-info/uuid.txt)
              bldst build add-failure ${BUILD_UUID} \
                --state 25 \
                --type "PACKER_BUILD_FAILED" \
                --message "Packer build failed - check logs for details"

  - task: ansible-configure
    config:
      platform: linux
      inputs:
        - name: build-info
        - name: ansible-playbooks
      run:
        path: sh
        args:
          - -c
          - |
            set -e
            BUILD_UUID=$(cat build-info/uuid.txt)
            
            bldst build add-state ${BUILD_UUID} --state 75 --status "Running Ansible configuration"
            
            ansible-playbook -i inventory ansible-playbooks/configure.yml
            
            bldst build add-state ${BUILD_UUID} --state 100 --status "Build completed successfully"

  - task: check-build-status
    config:
      platform: linux
      inputs:
        - name: build-info
      run:
        path: sh
        args:
          - -c
          - |
            BUILD_UUID=$(cat build-info/uuid.txt)
            
            # Get full build details
            bldst build get ${BUILD_UUID}
            
            # Check dashboard
            bldst dashboard recent --limit 5
```

### Simplified Pipeline with Error Handling

```yaml
- task: build-with-tracking
  config:
    platform: linux
    params:
      BLDST_API_URL: http://build-api.example.com
      BLDST_API_KEY: ((buildstate-api-key))
    run:
      path: bash
      args:
        - -c
        - |
          set -e
          
          # Setup
          bldst config set-url ${BLDST_API_URL}
          bldst auth set-key ${BLDST_API_KEY}
          
          # Initialize build tracking
          BUILD_UUID=$(initialize_build)  # Your function to create build
          
          # Trap to handle failures
          trap 'handle_failure ${BUILD_UUID}' ERR
          
          handle_failure() {
            local uuid=$1
            bldst build add-failure ${uuid} \
              --state $(get_current_state) \
              --type "PIPELINE_ERROR" \
              --message "Pipeline failed: ${BASH_COMMAND}"
          }
          
          # Your build steps with state updates
          bldst build add-state ${BUILD_UUID} --state 10 --status "Starting"
          # ... run your build commands ...
          bldst build add-state ${BUILD_UUID} --state 100 --status "Complete"
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `JWT_SECRET_KEY` | Secret key for JWT tokens | Randomly generated |
| `API_KEYS` | Comma-separated API keys | dev-key-12345 |
| `DATABASE_URL` | Database connection URL | /app/data/builds.db |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | JWT token expiration | 30 |

### Scaling

To scale the API service:

```bash
# Add more API instances
docker-compose up -d --scale api01=2 --scale api02=2 --scale api03=2

# Or use docker-compose scale
docker-compose up -d
docker-compose up -d --scale api01=3
```

## Development

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
uvicorn app.main:app --reload

# Run with environment file
export $(cat .env | xargs)
uvicorn app.main:app --reload
```

### Testing

#### Automated API Testing with Newman

The API includes comprehensive Postman collections for automated testing using Newman:

```bash
# Install Newman (if not already installed)
npm install -g newman

# Run all API tests (basic + synthetic transactions)
./test-api-newman.sh

# Or run individual test suites:
# Basic API tests
newman run --config newman-config.json

# Synthetic transaction tests (real-world scenarios)
newman run --config newman-synthetic-config.json
```

**Test Collections:**

1. **Basic API Tests** (`build-state-api-tests.postman_collection.json`)
   - Health checks
   - Authentication (JWT and IDM login)
   - User management (CRUD operations)
   - API token management
   - Build management
   - Dashboard monitoring

2. **Synthetic Transactions** (`build-state-synthetic-transactions.postman_collection.json`)
   - User onboarding flow
   - Complete build pipeline simulation
   - Failed build scenario
   - Dashboard monitoring
   - User deactivation flow

**Test Results:**
- Results are saved to JSON files: `test-results.json` and `synthetic-test-results.json`
- Install `jq` for formatted results: `brew install jq`

#### Manual Testing

```bash
# Run manual API tests
./test-api.sh

# Or run with pytest (if tests are added)
python -m pytest tests/
```

#### Import into Postman

1. Open Postman
2. Import the collection files:
   - `build-state-api-tests.postman_collection.json`
   - `build-state-synthetic-transactions.postman_collection.json`
3. Import the environment file:
   - `build-state-api-tests.postman_environment.json`
4. Update the `baseUrl` variable to match your setup

### Database Migration

For PostgreSQL migration:

1. Uncomment postgres service in `docker-compose.yml`
2. Update `DATABASE_URL` in `.env`
3. Create `init-db.sql` with schema
4. Run `docker-compose up --build`

## Monitoring

### Health Checks

- API containers: `http://localhost:8000/` (per container)
- Nginx: `http://localhost:8080/health`
- Load balancer status: Check container logs

### Logs

```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs nginx
docker-compose logs api01

# Follow logs
docker-compose logs -f api01
```

## Security

- Use strong JWT secrets and API keys
- Rotate keys regularly
- Use HTTPS in production
- Implement proper user management for JWT
- Monitor for suspicious activity

## Production Deployment

1. Use production-grade secrets
2. Configure HTTPS/TLS
3. Set up monitoring and alerting
4. Configure log aggregation
5. Implement backup strategy for database
6. Use managed database service
7. Configure resource limits

## Troubleshooting

### Common Issues

1. **API returns 401**: Check authentication headers
2. **Database connection failed**: Verify DATABASE_URL
3. **Nginx 502**: Check if API containers are healthy
4. **Build state not updating**: Verify build UUID

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=debug
docker-compose up --build
```

## API Documentation

### Interactive API Explorer

Once running, visit `http://localhost:8080/docs` for interactive Swagger/OpenAPI documentation.

![API Documentation Screenshot](screenshots/screencapture-build-state-docs-2026-02-15-10_02_23.png)

The interactive documentation provides:
- 🔍 Complete API reference with all endpoints
- 🧪 Try-it-out functionality to test endpoints directly
- 📝 Request/response schemas and examples
- 🔐 Authentication testing

### Recommended Usage

**For CI/CD Pipelines & Automation:** Use the `bldst` CLI tool
- Clean, maintainable commands
- Built-in error handling and retries
- Type-safe operations
- See examples throughout this document

**For Direct API Integration:** Use the REST API
- See [API_REFERENCE.md](API_REFERENCE.md) for complete endpoint documentation
- Interactive docs at `/docs` endpoint
- OpenAPI spec at `/openapi.json`

**For Exploration & Testing:** Use the interactive docs
- Navigate to `http://localhost:8080/docs`
- Authenticate using your API key or JWT token
- Test endpoints directly in your browser