# Build State API Service - Architecture Overview

> **💡 Recommended:** For pipeline integration, use the [`bldst` CLI tool](../../buildstate_cli/README.md) instead of direct API calls. See [README.md](README.md) for CLI examples.

## Overview

This implementation provides a scalable, containerized FastAPI service for managing multi-cloud IaaS image build states with JWT and API key authentication, designed specifically for integration with Concourse CI pipelines.

## Architecture Components

### 1. Horizontal Scaling with Docker Containers
- **3 API service instances** (`api01`, `api02`, `api03`) running FastAPI with Uvicorn
- **Nginx reverse proxy** for load balancing using least-connections algorithm
- **Shared volume** for SQLite database persistence across containers
- **Health checks** for automatic container recovery

### 2. Authentication & Security
- **JWT tokens** for session-based authentication
- **API keys** for pipeline integration (no SQL credentials needed)
- **Bearer token authentication** with automatic validation
- **Security headers** in Nginx configuration

### 3. Multi-Stage Docker Builds
- **Builder stage**: Installs Python dependencies in virtual environment
- **Runtime stage**: Minimal Python image with compiled dependencies
- **Security**: Non-root user, minimal attack surface
- **Performance**: Optimized layer caching and smaller final images

### 4. Database Layer
- **SQLite default**: File-based, zero-configuration, ACID compliant
- **PostgreSQL support**: Production-ready with connection pooling
- **Schema**: Normalized tables for platforms, OS versions, image types, builds, states, failures
- **Migrations**: Automatic schema initialization on startup

## Key Features

### ✅ Horizontal Scalability
- Multiple API containers behind load balancer
- Automatic health checking and failover
- Shared database with proper locking
- Easy scaling with `docker-compose up --scale`

### ✅ Pipeline-Friendly Authentication
```bash
# No SQL credentials in pipelines!
curl -H "X-API-Key: your-key" \
  http://api.example.com/builds/my-build/state
```

### ✅ JWT Authentication for UI/Admin Access
```bash
# Get token
TOKEN=$(curl -X POST /token -d '{"username":"user","password":"pass"}' | jq -r .access_token)

# Use token
curl -H "Authorization: Bearer $TOKEN" /dashboard/summary
```

### ✅ Comprehensive State Management
- State codes: 0-100 (increments of 5)
- Failure handling: Stay at failed state until manually reset
- Build lifecycle tracking with timestamps
- Platform-specific build organization

### ✅ Production-Ready Features
- Health checks and monitoring endpoints
- Structured logging and error handling
- CORS support for future web UI
- Environment-based configuration
- Docker Compose orchestration

## File Structure

```
api_service/
├── app/
│   └── main.py              # FastAPI application with auth & endpoints
├── nginx/
│   └── nginx.conf           # Load balancer configuration
├── Dockerfile               # Multi-stage API container build
├── nginx.Dockerfile         # Nginx container build
├── docker-compose.yml       # Service orchestration
├── requirements.txt         # Python dependencies
├── .env.example            # Environment template
├── test-api.sh             # Comprehensive test suite
├── init-db.sql             # PostgreSQL schema (optional)
├── Makefile                # Development commands
├── README.md               # Complete documentation
└── .dockerignore           # Docker build optimization
```

## Concourse Pipeline Integration

### Recommended: Using the bldst CLI

```yaml
jobs:
- name: build-image
  plan:
  - task: init-build
    config:
      platform: linux
      image_resource:
        type: registry-image
        source: {repository: your-registry/buildstate-cli}
      params:
        BLDST_API_URL: ((build-api-url))
        BLDST_API_KEY: ((build-api-key))
      outputs:
        - name: build-info
      run:
        path: sh
        args:
        - -c
        - |
          # Configure CLI
          bldst config set-url ${BLDST_API_URL}
          bldst auth set-key ${BLDST_API_KEY}
          
          # Get reference IDs (cache these if needed)
          PLATFORM_ID=$(bldst platform list --output json | jq -r '.[] | select(.name=="aws-commercial") | .id')
          OS_VERSION_ID=$(bldst os-version list --output json | jq -r '.[] | select(.version=="rhel-8.8") | .id')
          IMAGE_TYPE_ID=$(bldst image-type list --output json | jq -r '.[] | select(.name=="base") | .id')
          PROJECT_ID=$(bldst project list --output json | jq -r '.[] | select(.name=="platform") | .id')
          
          # Create build
          BUILD_UUID=$(bldst build create \
            --build-number "rhel-8.8-$(date +%s)" \
            --project-id ${PROJECT_ID} \
            --platform-id ${PLATFORM_ID} \
            --os-version-id ${OS_VERSION_ID} \
            --image-type-id ${IMAGE_TYPE_ID} \
            --output json | jq -r '.id')
          
          echo ${BUILD_UUID} > build-info/uuid.txt

  - task: packer-build
    config:
      inputs:
        - name: build-info
      run:
        path: sh
        args:
        - -c
        - |
          BUILD_UUID=$(cat build-info/uuid.txt)
          
          # Update state
          bldst build add-state ${BUILD_UUID} --state 10 --status "Starting Packer build"
          
          # Run packer
          packer build -var-file=vars.json template.json
          
          # Update on success
          bldst build add-state ${BUILD_UUID} --state 25 --status "Packer build completed"

  - task: ansible-configure
    config:
      inputs:
        - name: build-info
      run:
        path: sh
        args:
        - -c
        - |
          BUILD_UUID=$(cat build-info/uuid.txt)
          
          bldst build add-state ${BUILD_UUID} --state 50 --status "Starting Ansible configuration"
          ansible-playbook -i inventory playbook.yml
          bldst build add-state ${BUILD_UUID} --state 75 --status "Ansible configuration completed"

  - task: finalize-build
    config:
      inputs:
        - name: build-info
      run:
        path: sh
        args:
        - -c
        - |
          BUILD_UUID=$(cat build-info/uuid.txt)
          bldst build add-state ${BUILD_UUID} --state 100 --status "Build completed successfully"

  on_failure:
    do:
    - task: record-failure
      config:
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
              --type "PIPELINE_FAILURE" \
              --message "Pipeline failed at stage: ${FAILED_JOB}"
```

### Alternative: Direct API with curl

For environments where the CLI cannot be installed, see the full curl examples in the [README.md](README.md#concourse-pipeline-integration) (legacy approach).

## Deployment Options

### Development
```bash
make dev-cycle  # Clean, build, run, test
```

### Production
```bash
# Set environment variables
cp .env.example .env
nano .env  # Configure secrets

# Deploy
make build
make up
make health
```

### Scaling
```bash
# Scale to 6 API instances
make scale-up

# Check distribution
make ps
```

## Security Considerations

1. **API Keys**: Use strong, rotated keys for pipeline authentication
2. **JWT Secrets**: Use cryptographically secure secrets in production
3. **Network Security**: Configure firewall rules for API access
4. **HTTPS**: Implement TLS termination in production
5. **Monitoring**: Log authentication failures and suspicious activity
6. **Database**: Encrypt sensitive data at rest

## Monitoring & Observability

- **Health Endpoints**: `/health`, `/` for container health
- **Metrics**: Ready for Prometheus integration
- **Logs**: Structured logging with request IDs
- **Dashboard**: API provides build status summaries
- **Load Balancing**: Nginx status monitoring

## Future Enhancements

- **Web UI**: React dashboard for build monitoring
- **Webhooks**: Real-time notifications for state changes
- **Metrics**: Prometheus/Grafana integration
- **Caching**: Redis for API response caching
- **Rate Limiting**: Request throttling per API key
- **Audit Logging**: Complete audit trail for compliance

This architecture provides a robust, scalable foundation for managing complex multi-cloud image build pipelines while maintaining security and observability.