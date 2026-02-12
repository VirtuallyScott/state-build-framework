# Build State API Service - Architecture Overview

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

### Example Pipeline Usage

```yaml
jobs:
- name: build-image
  plan:
  - task: init-build
    config:
      run:
        path: sh
        args:
        - -c
        - |
          BUILD_ID="rhel-8.8-base-$(date +%s)"
          RESPONSE=$(curl -X POST ${API_URL}/builds \
            -H "X-API-Key: ${API_KEY}" \
            -H "Content-Type: application/json" \
            -d "{\"platform\":\"aws\",\"os_version\":\"rhel-8.8\",\"image_type\":\"base\",\"build_id\":\"${BUILD_ID}\"}")
          echo $RESPONSE | jq -r .id > build-uuid.txt

  - task: packer-build
    config:
      # ... packer configuration ...
      run:
        path: sh
        args:
        - -c
        - |
          BUILD_UUID=$(cat build-uuid.txt)

          # Update state to preparation
          curl -X POST ${API_URL}/builds/${BUILD_UUID}/state \
            -H "X-API-Key: ${API_KEY}" \
            -H "Content-Type: application/json" \
            -d '{"state_code": 10, "message": "Starting Packer build"}'

          # Run packer
          packer build -var-file=vars.json template.json

          # Update state on success
          curl -X POST ${API_URL}/builds/${BUILD_UUID}/state \
            -H "X-API-Key: ${API_KEY}" \
            -H "Content-Type: application/json" \
            -d '{"state_code": 25, "message": "Packer build completed"}'

  - task: ansible-configure
    config:
      run:
        path: sh
        args:
        - -c
        - |
          BUILD_UUID=$(cat build-uuid.txt)

          # Update state
          curl -X POST ${API_URL}/builds/${BUILD_UUID}/state \
            -H "X-API-Key: ${API_KEY}" \
            -H "Content-Type: application/json" \
            -d '{"state_code": 50, "message": "Starting Ansible configuration"}'

          # Run ansible
          ansible-playbook -i inventory playbook.yml

          # Update state
          curl -X POST ${API_URL}/builds/${BUILD_UUID}/state \
            -H "X-API-Key: ${API_KEY}" \
            -H "Content-Type: application/json" \
            -d '{"state_code": 75, "message": "Ansible configuration completed"}'

  - task: finalize-build
    config:
      run:
        path: sh
        args:
        - -c
        - |
          BUILD_UUID=$(cat build-uuid.txt)

          # Mark as complete
          curl -X POST ${API_URL}/builds/${BUILD_UUID}/state \
            -H "X-API-Key: ${API_KEY}" \
            -H "Content-Type: application/json" \
            -d '{"state_code": 100, "message": "Build completed successfully"}'

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
            curl -X POST ${API_URL}/builds/${BUILD_UUID}/failure \
              -H "X-API-Key: ${API_KEY}" \
              -H "Content-Type: application/json" \
              -d '{
                "error_message": "Pipeline failed",
                "error_code": "PIPELINE_FAILURE",
                "component": "concourse",
                "details": {"stage": "packer-build", "exit_code": 1}
              }'
```

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