#!/usr/bin/env bash
#
# Test script for the Build State API
# This script tests all endpoints with sample data
#
set -e

API_URL="http://localhost:8000"

echo "🧪 Testing Build State API"
echo "=========================="

# Wait for API to be ready
echo "⏳ Waiting for API to be ready..."
until curl -f -s "$API_URL/" > /dev/null; do
    echo "Waiting for API..."
    sleep 2
done

echo "✅ API is ready!"

# Test 1: Create a new build
echo ""
echo "📝 Test 1: Creating a new build"
BUILD_RESPONSE=$(curl -s -X POST "$API_URL/builds" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "aws",
    "os_version": "rhel-8.8",
    "image_type": "base",
    "build_id": "test-build-001",
    "pipeline_url": "https://concourse.example.com/pipelines/test",
    "commit_hash": "abc123def456"
  }')

BUILD_ID=$(echo $BUILD_RESPONSE | jq -r '.build_id')
echo "Created build: $BUILD_ID"

# Test 2: Transition state
echo ""
echo "🔄 Test 2: Transitioning state to 10 (Preparation)"
curl -s -X POST "$API_URL/builds/$BUILD_ID/state" \
  -H "Content-Type: application/json" \
  -d '{"state_code": 10, "message": "Starting preparation phase"}' | jq .

# Test 3: Get current state
echo ""
echo "📊 Test 3: Getting current state"
curl -s "$API_URL/builds/$BUILD_ID/state" | jq .

# Test 4: Record a failure
echo ""
echo "❌ Test 4: Recording a failure"
curl -s -X POST "$API_URL/builds/$BUILD_ID/failure" \
  -H "Content-Type: application/json" \
  -d '{
    "error_message": "Packer build failed: AMI creation timeout",
    "error_code": "PACKER_TIMEOUT",
    "component": "packer",
    "details": {"timeout_seconds": 3600, "attempt": 1}
  }' | jq .

# Test 5: Get build details
echo ""
echo "📋 Test 5: Getting build details"
curl -s "$API_URL/builds/$BUILD_ID" | jq .

# Test 6: Get dashboard summary
echo ""
echo "📈 Test 6: Getting dashboard summary"
curl -s "$API_URL/dashboard/summary" | jq .

# Test 7: Get recent builds
echo ""
echo "📅 Test 7: Getting recent builds"
curl -s "$API_URL/dashboard/recent" | jq .

# Test 8: Get builds by platform
echo ""
echo "🏷️  Test 8: Getting builds by platform (AWS)"
curl -s "$API_URL/dashboard/platform/aws" | jq .

echo ""
echo "🎉 All tests completed successfully!"
echo ""
echo "💡 Pipeline usage examples:"
echo "curl -X POST $API_URL/builds -H 'Content-Type: application/json' -d '{\"platform\":\"aws\",\"os_version\":\"rhel-8.8\",\"image_type\":\"base\",\"build_id\":\"my-build\"}'"
echo "curl -X POST $API_URL/builds/my-build/state -H 'Content-Type: application/json' -d '{\"state_code\":25,\"message\":\"Packer validation complete\"}'"
echo "curl $API_URL/builds/my-build/state | jq -r '.current_state'"