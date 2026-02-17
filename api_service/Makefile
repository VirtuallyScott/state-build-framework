# Makefile for Build State API Service

.PHONY: help build up down logs test clean dev prod

# Default target
help:
	@echo "Available commands:"
	@echo "  build     - Build Docker images"
	@echo "  up        - Start all services"
	@echo "  down      - Stop all services"
	@echo "  logs      - Show logs from all services"
	@echo "  test      - Run API tests"
	@echo "  clean     - Remove containers and volumes"
	@echo "  dev       - Start development environment"
	@echo "  prod      - Start production environment"

# Build Docker images
build:
	docker-compose -f docker/docker-compose.yml build

# Start all services
up:
	docker-compose -f docker/docker-compose.yml up -d

# Start with build
up-build: build up

# Stop all services
down:
	docker-compose -f docker/docker-compose.yml down

# Show logs
logs:
	docker-compose -f docker/docker-compose.yml logs -f

# Run tests
test:
	./tests/test-api-newman.sh

# Clean up
clean:
	docker-compose -f docker/docker-compose.yml down -v --remove-orphans
	docker system prune -f

# Development environment
dev:
	docker-compose -f docker/docker-compose.yml -f docker/docker-compose.dev.yml up -d

# Production environment (if you create docker-compose.prod.yml)
prod:
	docker-compose -f docker/docker-compose.yml -f docker/docker-compose.prod.yml up -d

# Quick development cycle
dev-cycle: down clean build up test

# Health check
health:
	@echo "Checking API health..."
	@curl -f http://localhost:8080/health && echo "✅ API is healthy" || echo "❌ API is not healthy"
	@echo "Checking API root..."
	@curl -f http://localhost:8080/ && echo "✅ API root is accessible" || echo "❌ API root is not accessible"

# Database operations
db-init:
	docker-compose -f docker/docker-compose.yml exec api01 python -c "from app.main import init_database; init_database(); print('Database initialized')"

# Scale API instances
scale-up:
	docker-compose -f docker/docker-compose.yml up -d --scale api01=2 --scale api02=2 --scale api03=2

scale-down:
	docker-compose -f docker/docker-compose.yml up -d --scale api01=1 --scale api02=1 --scale api03=1

# View running containers
ps:
	docker-compose -f docker/docker-compose.yml ps

# Execute commands in containers
shell-api:
	docker-compose -f docker/docker-compose.yml exec api01 /bin/bash

shell-nginx:
	docker-compose -f docker/docker-compose.yml exec nginx /bin/sh