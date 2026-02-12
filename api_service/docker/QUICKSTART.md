# Docker Quickstart Guide

This directory contains all Docker-related files for the Build State API service.

## Files

- `docker-compose.yml` - Main Docker Compose configuration for the complete stack
- `Dockerfile` - Multi-stage build for the Python API application
- `nginx.Dockerfile` - Nginx configuration for load balancing
- `.dockerignore` - Files to exclude from Docker builds

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- At least 2GB free RAM (recommended)

### Environment Setup

1. Copy the environment template:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your configuration:
   ```bash
   # Database
   POSTGRES_PASSWORD=your-secure-password

   # JWT Secret (generate a secure random string)
   JWT_SECRET_KEY=your-jwt-secret-key

   # API Keys (comma-separated)
   API_KEYS=dev-key-12345,prod-key-67890

   # Optional: Disable caching
   CACHE_ENABLED=true
   ```

### Start the Services

From the `api_service` directory (parent of this docker directory):

```bash
# Quick start with Makefile
make up

# Or manually:
docker-compose -f docker/docker-compose.yml up -d

# View logs
make logs
# or: docker-compose -f docker/docker-compose.yml logs -f

# Stop services
make down
# or: docker-compose -f docker/docker-compose.yml down
```

### Service URLs

- **API Load Balancer**: http://localhost:8080
- **Direct API instances**:
  - http://localhost:8001 (api01)
  - http://localhost:8002 (api02)
  - http://localhost:8003 (api03)
- **Nginx Status**: http://localhost:8080/nginx_status

### Health Checks

- **Overall Health**: http://localhost:8080/health
- **Readiness**: http://localhost:8080/ready
- **Status Dashboard**: http://localhost:8080/status

### Makefile Commands

The project includes a `Makefile` with convenient commands:

```bash
# Show all available commands
make help

# Development workflow
make build          # Build Docker images
make up            # Start all services
make up-build      # Build and start
make logs          # View logs
make test          # Run API tests
make health        # Check API health
make clean         # Clean up containers and volumes

# Container management
make ps            # View running containers
make shell-api     # Shell into API container
make shell-nginx   # Shell into Nginx container

# Scaling
make scale-up      # Scale API instances to 2 each
make scale-down    # Scale back to 1 each
```

## Architecture

The Docker setup includes:

- **3 API instances** (api01, api02, api03) for horizontal scaling
- **PostgreSQL database** with persistent data
- **Redis cache** for session and data caching
- **Nginx load balancer** with health checks

### Network

All services run on the `api-network` Docker network for secure communication.

## Development

### Rebuilding Images

```bash
# Rebuild all images
docker-compose -f docker/docker-compose.yml build --no-cache

# Rebuild specific service
docker-compose -f docker/docker-compose.yml build api01
```

### Database Management

The database data persists in a Docker volume. To reset:

```bash
# Stop services
docker-compose -f docker/docker-compose.yml down

# Remove volumes (WARNING: destroys data)
docker-compose -f docker/docker-compose.yml down -v

# Restart
docker-compose -f docker/docker-compose.yml up -d
```

### Logs and Debugging

```bash
# View all logs
docker-compose -f docker/docker-compose.yml logs

# View specific service logs
docker-compose -f docker/docker-compose.yml logs api01

# Follow logs in real-time
docker-compose -f docker/docker-compose.yml logs -f nginx
```

## Production Deployment

For production:

1. Use external PostgreSQL and Redis instances
2. Set strong passwords and secrets
3. Configure proper SSL/TLS termination
4. Set up monitoring and logging
5. Use Docker secrets for sensitive data

## Troubleshooting

### Common Issues

1. **Port conflicts**: Change ports in docker-compose.yml if 8080/8001-8003 are in use
2. **Memory issues**: Ensure Docker has enough RAM allocated
3. **Database connection**: Check POSTGRES_PASSWORD in .env file
4. **Build failures**: Clear Docker cache with `docker system prune`

### Health Check Failures

If services fail health checks:

```bash
# Check service status
docker-compose -f docker/docker-compose.yml ps

# Inspect failing container
docker-compose -f docker/docker-compose.yml exec api01 /bin/bash
```

## API Testing

Use the included Newman/Postman collections:

```bash
# From api_service/tests directory
./test-api-newman.sh
```

Or use the CLI tool:

```bash
# Install CLI
pip install ../buildstate_cli/

# Configure API URL
bldst_cli config set-url http://localhost:8080

# Check health
bldst_cli health
```