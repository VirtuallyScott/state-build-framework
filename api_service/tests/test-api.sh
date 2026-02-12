#!/bin/bash

# Test script for the Scalable Build State API
# Tests authentication, load balancing, and core functionality

set -e

API_URL="http://localhost:8080"
API_KEY="dev-key-12345"

echo "🧪 Testing Scalable Build State API"
echo "==================================="

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
until curl -f -s "$API_URL/health" > /dev/null; do
    echo "Waiting for API..."
    sleep 2
done

echo "✅ Services are ready!"

# Test 1: Health check
echo ""
echo "🏥 Test 1: Health check"
curl -s "$API_URL/health"

# Test 2: API root
echo ""
echo "📍 Test 2: API root endpoint"
curl -s "$API_URL/" | jq .

# Test 3: Get JWT token
echo ""
echo "🔑 Test 3: Getting JWT token"
TOKEN_RESPONSE=$(curl -s -X POST "$API_URL/token" \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass"}')

TOKEN=$(echo $TOKEN_RESPONSE | jq -r '.access_token')
echo "JWT Token obtained: ${TOKEN:0:20}..."

# Test 4: Create build with API key
echo ""
echo "📝 Test 4: Creating build with API key"
BUILD_RESPONSE=$(curl -s -X POST "$API_URL/builds" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "aws-commercial",
    "os_version": "rhel-8.8",
    "image_type": "base",
    "build_id": "test-build-001",
    "pipeline_url": "https://concourse.example.com/pipelines/test",
    "commit_hash": "abc123def456"
  }')

BUILD_ID=$(echo $BUILD_RESPONSE | jq -r '.id')
echo "Created build: $BUILD_ID"

# Test 5: Create build with JWT
echo ""
echo "🔐 Test 5: Creating build with JWT token"
BUILD_RESPONSE_JWT=$(curl -s -X POST "$API_URL/builds" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "azure",
    "os_version": "rhel-8.8",
    "image_type": "hana",
    "build_id": "test-build-jwt-001",
    "pipeline_url": "https://concourse.example.com/pipelines/test-jwt",
    "commit_hash": "def456ghi789"
  }')

BUILD_ID_JWT=$(echo $BUILD_RESPONSE_JWT | jq -r '.id')
echo "Created build with JWT: $BUILD_ID_JWT"

# Test 6: Transition state
echo ""
echo "🔄 Test 6: Transitioning state to 10 (Preparation)"
curl -s -X POST "$API_URL/builds/$BUILD_ID/state" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"state_code": 10, "message": "Starting preparation phase"}' | jq .

# Test 7: Get current state
echo ""
echo "📊 Test 7: Getting current state"
curl -s -H "X-API-Key: $API_KEY" \
  "$API_URL/builds/$BUILD_ID/state" | jq .

# Test 8: Record a failure
echo ""
echo "❌ Test 8: Recording a failure"
curl -s -X POST "$API_URL/builds/$BUILD_ID/failure" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "error_message": "Packer build failed: AMI creation timeout",
    "error_code": "PACKER_TIMEOUT",
    "component": "packer",
    "details": {"timeout_seconds": 3600, "attempt": 1}
  }' | jq .

# Test 9: Get build details
echo ""
echo "📋 Test 9: Getting build details"
curl -s -H "X-API-Key: $API_KEY" \
  "$API_URL/builds/$BUILD_ID" | jq .

# Test 10: Get dashboard summary
echo ""
echo "📈 Test 10: Getting dashboard summary"
curl -s -H "X-API-Key: $API_KEY" \
  "$API_URL/dashboard/summary" | jq .

# Test 11: Get recent builds
echo ""
echo "📅 Test 11: Getting recent builds"
curl -s -H "X-API-Key: $API_KEY" \
  "$API_URL/dashboard/recent" | jq .

# Test 12: Get builds by platform
echo ""
echo "🏷️  Test 12: Getting builds by platform (AWS)"
curl -s -H "X-API-Key: $API_KEY" \
  "$API_URL/dashboard/platform/aws-commercial" | jq .

# Test 13: Load balancing test
echo ""
echo "⚖️  Test 13: Load balancing test (multiple requests)"
for i in {1..5}; do
  echo "Request $i:"
  curl -s -w " -> Container: %{http_code}\n" \
    -H "X-API-Key: $API_KEY" \
    "$API_URL/dashboard/summary" | jq -r '.total_builds' | xargs echo "Total builds:"
done

# Test 14: Invalid authentication
echo ""
echo "🚫 Test 14: Testing invalid authentication"
curl -s -w "Status: %{http_code}\n" \
  "$API_URL/dashboard/summary" | tail -1

echo ""
echo "🎉 All tests completed successfully!"
echo ""
echo "💡 Pipeline integration examples:"
echo "curl -X POST $API_URL/builds -H 'X-API-Key: $API_KEY' -H 'Content-Type: application/json' -d '{\"platform\":\"aws\",\"os_version\":\"rhel-8.8\",\"image_type\":\"base\",\"build_id\":\"my-build\"}'"
echo "curl -X POST $API_URL/builds/\$BUILD_UUID/state -H 'X-API-Key: $API_KEY' -H 'Content-Type: application/json' -d '{\"state_code\":25,\"message\":\"Packer validation complete\"}'"
echo "curl -H 'X-API-Key: $API_KEY' $API_URL/builds/\$BUILD_UUID/state | jq -r '.current_state'"