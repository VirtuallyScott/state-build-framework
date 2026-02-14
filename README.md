# State-Based Build Framework

A complete framework for implementing resumable, state-based CI/CD pipelines for multi-cloud IaaS image creation. Includes both API service and CLI tools for managing build states across AWS, Azure, GCP, and private clouds.

## 🎯 What This Is

The **State-Based Build Framework** solves the critical problem of non-resumable build pipelines that lose all progress when interrupted. By implementing numerical state codes (0-100) and resumable workflows, this framework enables reliable, fault-tolerant image building across multiple cloud providers.

**Why State-Based?** Traditional monolithic pipelines fail completely on interruption. State-based pipelines can resume from any failure point, saving hours of rebuild time and ensuring consistent, reliable deployments.

## 📦 Components

### 1. API Service (`api_service/`)

FastAPI-based REST API for managing build states with authentication and authorization.

**Features:**
- ✅ JWT and API key authentication
- ✅ Scope-based authorization (read, write, admin)
- ✅ RESTful API for all resources
- ✅ Horizontal scaling with Nginx load balancer
- ✅ PostgreSQL/SQLite support
- ✅ Redis caching
- ✅ Comprehensive error handling
- ✅ Soft deletes for audit compliance
- ✅ Interactive API docs (Swagger/ReDoc)

**Quick Start:**
```bash
cd api_service/docker
docker compose up -d

# API available at http://localhost:8080
# Docs at http://localhost:8080/docs
```

**Documentation:**
- [API Reference](api_service/docs/API_REFERENCE.md) - Complete endpoint documentation
- [Authentication Guide](api_service/docs/AUTHENTICATION.md) - Auth & authorization
- [Architecture](api_service/docs/ARCHITECTURE.md) - System design
- [Deployment Guide](api_service/docs/README.md) - Production setup

### 2. CLI Tool (`buildstate_cli/`)

Modern command-line interface for managing build infrastructure.

**Features:**
- ✅ Type-safe Pydantic models
- ✅ Rich terminal output
- ✅ Secure credential storage (system keyring)
- ✅ JSON and table output formats
- ✅ Shell completion support
- ✅ Perfect for CI/CD integration

**Quick Start:**
```bash
cd buildstate_cli
pip install -e .

# Configure
bldst config set-url http://localhost:8080
bldst auth set-key dev-key-12345

# Use
bldst platform list
bldst os-version list
bldst build list
```

**Documentation:**
- [CLI Documentation](buildstate_cli/README.md) - Complete reference
- [Quick Start Guide](buildstate_cli/CLI_QUICKSTART.md) - 5-minute guide
- [Usage Examples](buildstate_cli/README.md#usage-examples) - Common workflows

### 3. Framework Documentation (`problem_statement/`)

Complete framework design, state definitions, and implementation guides.

**Documentation:**
- `index.md` - Framework overview
- `README.md` - Complete documentation
- `states.md` - State code definitions (0-100)
- `storage-implementation.md` - Storage architecture
- `sample-implementation.md` - AWS RHEL 8 example
- `failure-handling.md` - Failure recovery
- `QUICKSTART.md` - Step-by-step implementation guide

## 🚀 Quick Start

**📝 Need credentials?** See [CREDENTIALS.md](CREDENTIALS.md) for all URLs, API keys, and test user accounts.

### 1. Start the API

```bash
# Start all services (API, database, Redis, Nginx)
cd api_service/docker
docker compose up -d

# Verify services
docker compose ps
curl http://localhost:8080/health
```

### 2. Install the CLI

```bash
# Install CLI
cd buildstate_cli
pip install -e .

# Configure
bldst config set-url http://localhost:8080
bldst auth set-key dev-key-12345

# Test
bldst platform list
```

### 3. Create Your First Build

```bash
# List available resources
bldst platform list
bldst os-version list  
bldst image-type list

# Create a project
bldst project create \
  --name "rhel-9-base" \
  --description "RHEL 9 base images"

# View dashboard
curl -H "X-API-Key: dev-key-12345" http://localhost:8080/dashboard/summary
```

## 📚 Complete Documentation

### API Documentation
- **[API Reference](api_service/docs/API_REFERENCE.md)** - All endpoints, request/response schemas, examples
- **[Authentication Guide](api_service/docs/AUTHENTICATION.md)** - JWT tokens, API keys, scopes, best practices
- **[Architecture Overview](api_service/docs/ARCHITECTURE.md)** - System design, scaling, database
- **[Deployment Guide](api_service/docs/README.md)** - Production deployment, Docker, configuration

### CLI Documentation
- **[CLI Documentation](buildstate_cli/README.md)** - Complete command reference
- **[Quick Start Guide](buildstate_cli/CLI_QUICKSTART.md)** - Get started fast
- **[API Integration](buildstate_cli/README.md#cicd-integration)** - CI/CD examples

### Framework Documentation
- **[Framework Overview](problem_statement/README.md)** - Complete framework design
- **[Quick Start](problem_statement/QUICKSTART.md)** - Implementation guide
- **[State Definitions](problem_statement/states.md)** - State codes 0-100
- **[Storage Implementation](problem_statement/storage-implementation.md)** - Database design
- **[Sample Implementation](problem_statement/sample-implementation.md)** - Worked example
- **[Failure Handling](problem_statement/failure-handling.md)** - Recovery strategies

### CI/CD & DevOps
- **[CI/CD Pipeline](docs/CI_CD_PIPELINE.md)** - Automated builds, semantic versioning, container registry
- **[Resumable Builds Design](docs/RESUMABLE_BUILDS_DESIGN.md)** - Advanced resumability architecture
- **[Resumable Builds Quick Start](docs/RESUMABLE_BUILDS_QUICKSTART.md)** - Usage guide
- **[Documentation Index](docs/INDEX.md)** - Complete documentation hub

## 🎓 Key Concepts

### State Codes (0-100)
Build progress is tracked with numerical codes in increments of 5:
- **0** - Pending/Not started
- **5-15** - Preparation and validation
- **20-45** - Image building (Packer)
- **50-75** - Configuration (Ansible)
- **80-95** - Testing and validation
- **100** - Completed

### Authorization Scopes
Three permission levels control API access:
- **read** - View resources (monitoring, dashboards)
- **write** - Create and update (build pipelines)
- **admin** - Delete resources (maintenance)

### Soft Deletes
Resources are never permanently deleted. They're marked with `deactivated_at` timestamp for audit compliance.

### Multi-Cloud Support
Single API manages builds across:
- AWS (commercial, GovCloud, China)
- Azure (commercial, government)
- Google Cloud Platform
- Oracle Cloud
- Private clouds (OpenStack, etc.)

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Nginx Load Balancer                 │
│                    (localhost:8080)                     │
└────────────────┬───────────────┬───────────────┬────────┘
                 │               │               │
         ┌───────▼──────┐ ┌─────▼──────┐ ┌─────▼──────┐
         │   API 01     │ │   API 02   │ │   API 03   │
         │ (FastAPI)    │ │ (FastAPI)  │ │ (FastAPI)  │
         └──────┬───────┘ └─────┬──────┘ └─────┬──────┘
                │               │               │
                └───────────────┴───────────────┘
                                │
                    ┌───────────┴────────────┐
                    │                        │
            ┌───────▼────────┐      ┌───────▼──────┐
            │   PostgreSQL   │      │    Redis     │
            │   (Database)   │      │   (Cache)    │
            └────────────────┘      └──────────────┘
```

## 💡 Usage Examples

### API Direct Usage

```bash
# Authenticate with API key
export API_KEY="dev-key-12345"
export API_URL="http://localhost:8080"

# List platforms
curl -H "X-API-Key: $API_KEY" $API_URL/platforms/

# Create a build
curl -X POST $API_URL/builds \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "rhel-9",
    "platform_id": "aws-commercial",
    "os_version_id": "rhel-9.3",
    "image_type_id": "base",
    "build_number": "2024.02.001"
  }'

# Update build state
curl -X POST $API_URL/builds/{build-id}/state \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "state_code": 25,
    "status": "in_progress",
    "message": "Installing packages"
  }'
```

### CLI Usage

```bash
# Configure once
bldst config set-url http://localhost:8080
bldst auth set-key dev-key-12345

# Create resources
bldst platform create --name "Production AWS" --cloud-provider aws --region us-east-1
bldst os-version create --name "Ubuntu" --version "22.04"
bldst image-type create --name "web-server" --description "Nginx web server"

# Query resources
bldst platform list --output json | jq '.[] | select(.cloud_provider == "aws")'

# Manage builds
bldst build list --status in_progress
bldst build get {build-id}
```

### CI/CD Integration (Concourse)

```yaml
resources:
  - name: buildstate-api
    type: http-api
    source:
      uri: ((buildstate-api-url))
      headers:
        X-API-Key: ((buildstate-api-key))

jobs:
  - name: build-image
    plan:
      - task: create-build
        config:
          run:
            path: bash
            args:
              - -c
              - |
                # Install CLI
                pip install -e buildstate_cli
                
                # Configure
                bldst config set-url $API_URL
                bldst auth set-key $API_KEY
                
                # Create build
                BUILD_ID=$(bldst build create \
                  --project-id rhel-9 \
                  --platform-id aws-commercial \
                  --os-version-id rhel-9.3 \
                  --image-type-id base \
                  --build-number $BUILD_NUMBER \
                  --output json | jq -r '.id')
                
                echo $BUILD_ID > build-id.txt
        params:
          API_URL: ((buildstate-api-url))
          API_KEY: ((buildstate-api-key))
```

## 🔒 Security

### Test Credentials (Development Only)

**API Keys:**
- `readonly-key-888` - Read-only access
- `dev-key-12345` - Read + write access
- `admin-key-99999` - Full admin access

**Users:**
- Username: `admin`, Password: `admin123` (admin scope)
- Username: `user`, Password: `user123` (write scope)
- Username: `readonly`, Password: `readonly123` (read scope)

**⚠️ Change these in production!**

### Production Security
- Use HTTPS/TLS for all API communication
- Store API keys in secret managers (Vault, AWS Secrets Manager, etc.)
- Rotate keys regularly
- Use least-privilege principle
- Enable audit logging
- Monitor authentication failures

## 🧪 Testing

### API Tests

```bash
cd api_service
pytest tests/

# Or with coverage
pytest --cov=app tests/
```

### CLI Tests

```bash
cd buildstate_cli
pytest tests/
```

### Integration Tests

```bash
# Start services
cd api_service/docker
docker compose up -d

# Run tests
cd ../tests
./test-api.sh
```

## 📊 State Code Reference

Quick reference for common state codes:

| Code | Category | Description |
|------|----------|-------------|
| 0 | Init | Build pending |
| 5 | Prep | Environment preparation |
| 10 | Prep | Dependencies validated |
| 15 | Prep | Configuration validated |
| 20 | Build | Packer build started |
| 25 | Build | Base image created |
| 30 | Build | Packages installing |
| 40 | Build | Packer build complete |
| 50 | Config | Ansible started |
| 60 | Config | System configuration |
| 70 | Config | Application configuration |
| 75 | Config | Ansible complete |
| 80 | Test | Testing started |
| 90 | Test | Tests passed |
| 95 | Finalize | Creating artifacts |
| 100 | Complete | Build successful |

See [states.md](problem_statement/states.md) for complete definitions.

## 🚀 Deployment

### Development

```bash
# Start all services
cd api_service/docker
docker compose up -d
```

### Production

See [Deployment Guide](api_service/docs/README.md) for:
- Production Docker configuration
- Database setup (PostgreSQL)
- SSL/TLS configuration
- Scaling guidelines
- Monitoring setup
- Backup strategies

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with tests
4. Run tests and linting
5. Commit changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📝 License

MIT License - see LICENSE file for details.

## 🆘 Support

- **Documentation**: See links above for complete documentation
- **API Issues**: Check [API Reference](api_service/docs/API_REFERENCE.md) and [Authentication Guide](api_service/docs/AUTHENTICATION.md)
- **CLI Issues**: Check [CLI Documentation](buildstate_cli/README.md)
- **Framework Questions**: See [problem_statement/README.md](problem_statement/README.md)

## 🗺️ Roadmap

- [ ] GraphQL API support
- [ ] Real-time state updates (WebSocket)
- [ ] Advanced metrics and monitoring
- [ ] Build artifact storage integration
- [ ] Multi-region API deployment
- [ ] Enhanced CLI with progress bars
- [ ] Web UI dashboard

---

**Built for reliable, resumable multi-cloud image builds** 🚀

### 2. Install the CLI

```bash
# Install CLI
cd buildstate_cli
pip install -e .

# Configure
bldst config set-url http://localhost:8080
bldst auth set-key dev-key-12345

# Test
bldst platform list
```

### 3. Create Your First Build

```bash
# List available resources
bldst platform list
bldst os-version list  
bldst image-type list

# Create a project
bldst project create \
  --name "rhel-9-base" \
  --description "RHEL 9 base images"

# View dashboard
curl -H "X-API-Key: dev-key-12345" http://localhost:8080/dashboard/summary
```

## 📚 Complete Documentation

### API Documentation
- **[API Reference](api_service/docs/API_REFERENCE.md)** - All endpoints, request/response schemas, examples
- **[Authentication Guide](api_service/docs/AUTHENTICATION.md)** - JWT tokens, API keys, scopes, best practices
- **[Architecture Overview](api_service/docs/ARCHITECTURE.md)** - System design, scaling, database
- **[Deployment Guide](api_service/docs/README.md)** - Production deployment, Docker, configuration

### CLI Documentation
- **[CLI Documentation](buildstate_cli/README.md)** - Complete command reference
- **[Quick Start Guide](buildstate_cli/CLI_QUICKSTART.md)** - Get started fast
- **[API Integration](buildstate_cli/README.md#cicd-integration)** - CI/CD examples

### Framework Documentation
- **[Framework Overview](problem_statement/README.md)** - Complete framework design
- **[Quick Start](problem_statement/QUICKSTART.md)** - Implementation guide
- **[State Definitions](problem_statement/states.md)** - State codes 0-100
- **[Storage Implementation](problem_statement/storage-implementation.md)** - Database design
- **[Sample Implementation](problem_statement/sample-implementation.md)** - Worked example
- **[Failure Handling](problem_statement/failure-handling.md)** - Recovery strategies

## 🎓 Key Concepts