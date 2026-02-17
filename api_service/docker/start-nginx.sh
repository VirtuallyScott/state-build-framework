#!/bin/sh

# Wait for API services to be available
echo "Waiting for API services to be ready..."

# Function to check if a service is responding
check_service() {
    local service=$1
    local max_attempts=30
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        echo "Checking $service (attempt $attempt/$max_attempts)..."
        if curl -f --max-time 5 "$service" >/dev/null 2>&1; then
            echo "$service is ready!"
            return 0
        fi
        sleep 2
        attempt=$((attempt + 1))
    done

    echo "ERROR: $service did not become ready after $max_attempts attempts"
    return 1
}

# Wait for all API services
check_service "http://api01:8000/health" || exit 1
check_service "http://api02:8000/health" || exit 1
check_service "http://api03:8000/health" || exit 1

echo "All API services are ready. Starting nginx..."
exec nginx -g "daemon off;"