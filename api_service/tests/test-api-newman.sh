#!/usr/bin/env bash
#
# Build State API Newman Tests
# This script runs comprehensive API tests using Newman
#
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

echo "🚀 Starting Build State API Newman Tests"
echo "=========================================="

# Check if Docker Compose is running
if ! docker-compose -f docker/docker-compose.yml ps | grep -q "Up"; then
    echo "❌ Docker Compose services are not running. Please start them first from the 'docker' directory:"
    echo "   cd docker && docker-compose up -d"
    exit 1
fi

# Wait for API to be ready
echo "⏳ Waiting for API to be ready..."
max_attempts=30
attempt=1

while [ $attempt -le $max_attempts ]; do
    if curl -s -f http://127.0.0.1:8000/health/liveness > /dev/null 2>&1; then
        echo "✅ API is ready!"
        break
    fi

    echo "Attempt $attempt/$max_attempts: API not ready yet..."
    sleep 2
    ((attempt++))
done

if [ $attempt -gt $max_attempts ]; then
    echo "❌ API failed to start within expected time"
    exit 1
fi

# Check if Newman is installed
if ! command -v newman &> /dev/null; then
    echo "❌ Newman is not installed. Installing..."
    if command -v npm &> /dev/null; then
        npm install -g newman
    else
        echo "❌ npm is not available. Please install Node.js and npm first."
        exit 1
    fi
fi

# Run basic API tests
echo ""
echo "🧪 Running Basic API Tests..."
newman run tests/build-state-api-tests.postman_collection.json \
  --reporters cli,json \
  --reporter-json-export tests/test-results.json \
  --timeout 30000 \
  --delay-request 1000 \
  --suppress-exit-code false

basic_tests_result=$?

if [ $basic_tests_result -eq 0 ]; then
    echo "✅ Basic API tests passed!"
else
    echo "❌ Basic API tests failed!"
fi

# Run synthetic transaction tests
echo ""
echo "🎭 Running Synthetic Transaction Tests..."
newman run tests/build-state-synthetic-transactions.postman_collection.json \
  --environment tests/build-state-api-tests.postman_environment.json \
  --reporters cli,json \
  --reporter-json-export tests/synthetic-test-results.json \
  --timeout 30000 \
  --delay-request 500 \
  --suppress-exit-code false

synthetic_tests_result=$?

if [ $synthetic_tests_result -eq 0 ]; then
    echo "✅ Synthetic transaction tests passed!"
else
    echo "❌ Synthetic transaction tests failed!"
fi

# Overall results
echo ""
echo "📊 Test Results Summary:"
echo "========================"

if command -v jq &> /dev/null; then
    echo "Basic Tests:"
    if [ -f "test-results.json" ]; then
        jq -r '.run.stats | "  Total: \(.requests.total), Passed: \(.requests.total - .requests.failed), Failed: \(.requests.failed)"' test-results.json
    fi

    echo "Synthetic Tests:"
    if [ -f "synthetic-test-results.json" ]; then
        jq -r '.run.stats | "  Total: \(.requests.total), Passed: \(.requests.total - .requests.failed), Failed: \(.requests.failed)"' synthetic-test-results.json
    fi
else
    echo "Install jq for detailed results: brew install jq"
fi

# Final status
if [ $basic_tests_result -eq 0 ] && [ $synthetic_tests_result -eq 0 ]; then
    echo ""
    echo "🎉 All tests passed successfully!"
    echo ""
    echo "📁 Test results saved to:"
    echo "   - Basic tests: ./test-results.json"
    echo "   - Synthetic tests: ./synthetic-test-results.json"
    exit 0
else
    echo ""
    echo "❌ Some tests failed!"
    echo ""
    echo "📁 Check test results in:"
    echo "   - Basic tests: ./test-results.json"
    echo "   - Synthetic tests: ./synthetic-test-results.json"
    exit 1
fi