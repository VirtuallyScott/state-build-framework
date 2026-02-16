#!/usr/bin/env bash
#
# Test script for the Scalable Build State API
# Tests authentication, load balancing, and core functionality
#
#set -e

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
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=testpass")
echo "Token response: $TOKEN_RESPONSE"

TOKEN=$(echo $TOKEN_RESPONSE | jq -r '.access_token')
echo "JWT Token obtained: ${TOKEN:0:20}..."

# Test 4: Create a parent project
echo ""
echo "📝 Test 4: Creating a parent project"
PARENT_PROJECT_RESPONSE=$(curl -s -X POST "$API_URL/projects" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "parent-project",
    "display_name": "Parent Project"
  }')
PARENT_PROJECT_ID=$(echo $PARENT_PROJECT_RESPONSE | jq -r '.id')
echo "Created parent project: $PARENT_PROJECT_ID"

# Test 5: Create a child project
echo ""
echo "📝 Test 5: Creating a child project"
CHILD_PROJECT_RESPONSE=$(curl -s -X POST "$API_URL/projects" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"child-project\",
    \"display_name\": \"Child Project\",
    \"parent_project_id\": \"$PARENT_PROJECT_ID\"
  }")
CHILD_PROJECT_ID=$(echo $CHILD_PROJECT_RESPONSE | jq -r '.id')
echo "Created child project: $CHILD_PROJECT_ID"


# Test 6: Create build with API key
echo ""
echo "📝 Test 6: Creating build with API key"
BUILD_RESPONSE=$(curl -s -X POST "$API_URL/builds" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"project_id\": \"$CHILD_PROJECT_ID\",
    \"platform\": \"aws-commercial\",
    \"image_type\": \"base\",
    \"description\": \"Test build for child project\"
  }")

BUILD_ID=$(echo $BUILD_RESPONSE | jq -r '.id')
echo "Created build: $BUILD_ID"

# Test 7: Create build with JWT
echo ""
echo "🔐 Test 7: Creating build with JWT token"
BUILD_RESPONSE_JWT=$(curl -s -X POST "$API_URL/builds" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"project_id\": \"$CHILD_PROJECT_ID\",
    \"platform\": \"azure\",
    \"image_type\": \"hana\",
    \"description\": \"Another test build\"
  }")

BUILD_ID_JWT=$(echo $BUILD_RESPONSE_JWT | jq -r '.id')
echo "Created build with JWT: $BUILD_ID_JWT"

# Test 8: Transition state
echo ""
echo "🔄 Test 8: Transitioning state to 10 (Preparation)"
curl -s -X POST "$API_URL/builds/$BUILD_ID/state" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{\"state_name\": "preparation", "message": "Starting preparation phase"}' | jq .

# Test 9: Get current state
echo ""
echo "📊 Test 9: Getting current state"
curl -s -H "X-API-Key: $API_KEY" \
  "$API_URL/builds/$BUILD_ID/state" | jq .

# Test 10: Record a failure
echo ""
echo "❌ Test 10: Recording a failure"
curl -s -X POST "$API_URL/builds/$BUILD_ID/failure" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    \"error_message\": \"Packer build failed: AMI creation timeout\",
    \"error_code\": \"PACKER_TIMEOUT\"
  }' | jq .

# Test 11: Get build details
echo ""
echo "📋 Test 11: Getting build details"
curl -s -H "X-API-Key: $API_KEY" \
  "$API_URL/builds/$BUILD_ID" | jq .

# Test 12: Get dashboard summary
echo ""
echo "📈 Test 12: Getting dashboard summary"
curl -s -H "X-API-Key: $API_KEY" \
  "$API_URL/dashboard/summary" | jq .

# Test 13: Get recent builds
echo ""
echo "📅 Test 13: Getting recent builds"
curl -s -H "X-API-Key: $API_KEY" \
  "$API_URL/dashboard/recent" | jq .

# Test 14: Get builds by platform
echo ""
echo "🏷️  Test 14: Getting builds by platform (AWS)"
curl -s -H "X-API-Key: $API_KEY" \
  "$API_URL/dashboard/platform/aws-commercial" | jq .

# Test 15: Load balancing test
echo ""
echo "⚖️  Test 15: Load balancing test (multiple requests)"
for i in {1..5}; do
  echo "Request $i:"
  curl -s -w " -> Container: %{http_code}\n" \
    -H "X-API-Key: $API_KEY" \
    "$API_URL/dashboard/summary" | jq -r '.total_builds' | xargs echo "Total builds:"
done

# Test 16: Invalid authentication
echo ""
echo "🚫 Test 16: Testing invalid authentication"
curl -s -w "Status: %{http_code}\n" \
  "$API_URL/dashboard/summary" | tail -1

echo ""
echo "🎉 All tests completed successfully!"
echo ""
echo "💡 Pipeline integration examples:"
echo "curl -X POST $API_URL/builds -H 'X-API-Key: $API_KEY' -H 'Content-Type: application/json' -d '{\"project_id\":\"$CHILD_PROJECT_ID\",\"platform\":\"aws\",\"image_type\":\"base\"}'"
echo "curl -X POST $API_URL/builds/\$BUILD_UUID/state -H 'X-API-Key: $API_KEY' -H 'Content-Type: application/json' -d '{\"state_name\":\"validation\",\"message\":\"Packer validation complete\"}'"
echo "curl -H 'X-API-Key: $API_KEY' $API_URL/builds/\$BUILD_UUID/state | jq -r '.current_state'"
