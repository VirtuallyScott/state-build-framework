# Build API Service Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy database schema and sample data
COPY database-schema.sql sample-data.sql ./

# Copy API code
COPY build-api.py .

# Create data directory
RUN mkdir -p /app/data

# Set environment variable for database location
ENV DATABASE_URL=/app/data/builds.db

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Run the API server
CMD ["uvicorn", "build-api:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]