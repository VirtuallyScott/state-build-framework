# Build State API Service

A scalable, containerized FastAPI service for managing multi-cloud IaaS image build states with JWT and API key authentication.

## Architecture

- **Horizontal Scaling**: Multiple API containers behind Nginx load balancer
- **Authentication**: JWT tokens and API keys
- **Database**: SQLite (default) or PostgreSQL
- **Caching**: Redis for dashboard caching and session management
- **Containerization**: Multi-stage Docker builds
- **Load Balancing**: Nginx with least-connections algorithm

## Database Configuration

The API supports both SQLite and PostgreSQL databases. Database type is configured via environment variables:

### Environment Variables

- `ENVIRONMENT`: `production` (default), `development`, `staging` - Controls dummy data loading
- `DATABASE_TYPE`: `auto` (default), `sqlite`, or `postgresql`
- `DATABASE_URL`: Database connection string

### Auto-Detection

When `DATABASE_TYPE=auto`, the database type is automatically detected from `DATABASE_URL`:

- `postgresql://user:pass@host:port/db` → PostgreSQL
- `postgres://user:pass@host:port/db` → PostgreSQL
- `sqlite:///path/to/db.db` → SQLite
- `path/to/db.db` → SQLite (fallback)

### Examples

**SQLite (default):**
```bash
DATABASE_TYPE=auto
DATABASE_URL=sqlite:///builds.db
```

**PostgreSQL:**
```bash
DATABASE_TYPE=postgresql
DATABASE_URL=postgresql://user:password@localhost:5432/builds
```

**Docker Compose (PostgreSQL):**
```bash
cd docker
DATABASE_TYPE=postgresql docker-compose up
```

### Switching Databases

You can switch between SQLite and PostgreSQL without rebuilding the application:

1. Set `DATABASE_TYPE` to the desired database
2. Update `DATABASE_URL` to point to the new database
3. Restart the application

The same container image works for both database types.
- ✅ Health checks and monitoring
- ✅ SQLite/PostgreSQL support
- ✅ Multi-stage Docker builds
- ✅ Comprehensive error handling

## Dummy Data

The application automatically loads comprehensive dummy data when running in development mode. This includes:

- **Users & Profiles**: Admin user, test users, and employee profiles
- **API Tokens**: Authentication tokens with different permission scopes
- **Platforms**: AWS, Azure, GCP, and other cloud providers
- **OS Versions**: Various Linux distributions and versions
- **Image Types**: Base images, SAP HANA, web servers, databases, etc.
- **Build Records**: Sample build jobs with different states
- **Build States**: Success, failed, running, and cancelled builds
- **Build Failures**: Detailed error information for failed builds

### Loading Dummy Data

Set the `ENVIRONMENT` variable to `development` to automatically load dummy data on startup:

```bash
# Environment variable
ENVIRONMENT=development

# Or in docker-compose.yml
environment:
  - ENVIRONMENT=development
```

The dummy data is loaded from `dummy-data.sql` and includes realistic sample data for testing and development.

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Git

### Development Setup with Dummy Data

1. **Start the services:**
   ```bash
   cd docker
   docker-compose up --build -d
   ```

2. **Verify services are running:**
   ```bash
   docker-compose ps
   ```

3. **Check logs:**
   ```bash
   docker-compose logs api01
   ```

4. **Test the API:**
   ```bash
   # Health check (no auth required)
   curl http://localhost:8080/health

   # Get dashboard summary (requires API key)
   curl -H "X-API-Key: dev-key-12345" http://localhost:8080/dashboard/summary

   # Get recent builds
   curl -H "X-API-Key: dev-key-12345" http://localhost:8080/dashboard/recent
   ```

### Environment Variables

- `ENVIRONMENT=development`: Enables automatic loading of dummy data on startup
- `API_KEYS`: Comma-separated list of valid API keys (default: "dev-key-12345,prod-key-67890")

### Dummy Data

When `ENVIRONMENT=development`, the API automatically loads comprehensive dummy data including:
- 10 sample builds across AWS, Azure, and Google Cloud platforms
- Multiple image types (Base Image, SAP HANA, Web Server, etc.)
- User accounts and API tokens
- Platform and OS version configurations
- Build states and failure records

## API Usage

### Authentication

#### JWT Token
```bash
# Get JWT token
curl -X POST http://localhost:8080/token \
  -H "Content-Type: application/json" \
  -d '{"username": "your-user", "password": "your-password"}'

# Use token in requests
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:8080/dashboard/summary
```

#### API Key
```bash
# Use API key in requests
curl -H "X-API-Key: your-api-key" \
  http://localhost:8080/dashboard/summary
```

### Core Endpoints

#### Create Build
```bash
curl -X POST http://localhost:8080/builds \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "aws-commercial",
    "os_version": "rhel-8.8",
    "image_type": "base",
    "build_id": "my-build-001",
    "pipeline_url": "https://concourse.example.com/pipelines/my-pipeline",
    "commit_hash": "abc123def456"
  }'
```

#### Update Build State
```bash
curl -X POST http://localhost:8080/builds/{build-uuid}/state \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "state_code": 25,
    "message": "Packer build completed successfully"
  }'
```

#### Record Failure
```bash
curl -X POST http://localhost:8080/builds/{build-uuid}/failure \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "error_message": "Packer build failed: AMI creation timeout",
    "error_code": "PACKER_TIMEOUT",
    "component": "packer",
    "details": {"timeout_seconds": 3600, "attempt": 1}
  }'
```

#### Get Build Details
```bash
curl -H "X-API-Key: your-api-key" \
  http://localhost:8080/builds/{build-uuid}
```

#### Get Current State
```bash
curl -H "X-API-Key: your-api-key" \
  http://localhost:8080/builds/{build-uuid}/state
```

#### Dashboard Endpoints
```bash
# Summary
curl -H "X-API-Key: your-api-key" \
  http://localhost:8080/dashboard/summary

# Recent builds
curl -H "X-API-Key: your-api-key" \
  http://localhost:8080/dashboard/recent

# Builds by platform
curl -H "X-API-Key: your-api-key" \
  http://localhost:8080/dashboard/platform/aws-commercial
```

### Health and Status Endpoints

#### Health Check
```bash
curl http://localhost:8080/health
# Returns: {"status": "healthy"}
```

#### Readiness Check
Checks database and Redis connectivity for end-to-end functionality:
```bash
curl http://localhost:8080/ready
# Returns: {
#   "database": true,
#   "redis": true,
#   "overall": true
# }
```

#### Comprehensive Status
Shows health of all components (API servers, database, Redis):
```bash
curl http://localhost:8080/status
# Returns: {
#   "overall_status": "healthy",
#   "timestamp": "2024-01-15T10:30:00.000000",
#   "components": [
#     {"name": "api-local", "status": "healthy", "details": "OK"},
#     {"name": "database", "status": "healthy", "details": "PostgreSQL connection"},
#     {"name": "redis", "status": "healthy", "details": "Redis cache"},
#     {"name": "api01", "status": "healthy", "details": "HTTP 200"},
#     {"name": "api02", "status": "healthy", "details": "HTTP 200"},
#     {"name": "api03", "status": "healthy", "details": "HTTP 200"}
#   ]
# }
```

#### Status Server
Access comprehensive status via dedicated server (requires /etc/hosts entry):
```bash
# Add to /etc/hosts: 127.0.0.1 status.localbuild.api
curl http://status.localbuild.api/
# Returns the same comprehensive status as /status endpoint
```

## Concourse Pipeline Integration

### Example Pipeline Task

```yaml
- task: create-build
  config:
    platform: linux
    image_resource:
      type: registry-image
      source:
        repository: curlimages/curl
        tag: latest
    run:
      path: sh
      args:
        - -c
        - |
          BUILD_ID="my-build-$(date +%s)"
          RESPONSE=$(curl -X POST http://build-api.example.com/builds \
            -H "X-API-Key: ${API_KEY}" \
            -H "Content-Type: application/json" \
            -d "{\"platform\":\"aws\",\"os_version\":\"rhel-8.8\",\"image_type\":\"base\",\"build_id\":\"${BUILD_ID}\"}")
          echo "Build created: $RESPONSE"

- task: update-state
  config:
    platform: linux
    image_resource:
      type: registry-image
      source:
        repository: curlimages/curl
        tag: latest
    run:
      path: sh
      args:
        - -c
        - |
          BUILD_UUID=$(cat build-uuid.txt)
          curl -X POST http://build-api.example.com/builds/${BUILD_UUID}/state \
            -H "X-API-Key: ${API_KEY}" \
            -H "Content-Type: application/json" \
            -d '{"state_code": 25, "message": "Packer validation complete"}'

- task: check-state
  config:
    platform: linux
    image_resource:
      type: registry-image
      source:
        repository: curlimages/curl
        tag: latest
    run:
      path: sh
      args:
        - -c
        - |
          BUILD_UUID=$(cat build-uuid.txt)
          STATE=$(curl -H "X-API-Key: ${API_KEY}" \
            http://build-api.example.com/builds/${BUILD_UUID}/state | jq -r '.current_state')
          echo "Current state: $STATE"
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
../scripts/test-api.sh

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

Once running, visit `http://localhost:8080/docs` for interactive API documentation.