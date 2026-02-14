#!/bin/bash
# Test script for BuildState CLI with API authentication and CRUD operations

set -e

API_URL="http://localhost:8080"
API_KEY="dev-key-12345"
ADMIN_KEY="admin-key-99999"
READONLY_KEY="readonly-key-888"

echo "🔧 Setting up CLI configuration..."
buildctl config set-url "$API_URL"
buildctl config set-key "$API_KEY"

echo ""
echo "✅ Testing authentication..."
buildctl health check || { echo "❌ API health check failed"; exit 1; }

echo ""
echo "📋 Testing Platform CRUD..."
echo "  - Listing platforms..."
buildctl platform list

echo "  - Creating new platform..."
PLATFORM_ID=$(buildctl platform create \
  --name "CLI Test Platform" \
  --cloud-provider "test-cloud" \
  --region "test-region" \
  --output json | jq -r '.id')

echo "  - Platform created with ID: $PLATFORM_ID"

echo "  - Getting platform details..."
buildctl platform get "$PLATFORM_ID"

echo "  - Updating platform..."
buildctl platform update "$PLATFORM_ID" \
  --name "CLI Test Platform Updated" \
  --region "test-region-updated"

echo "  - Deleting platform (requires admin key)..."
buildctl config set-key "$ADMIN_KEY"
buildctl platform delete "$PLATFORM_ID"
buildctl config set-key "$API_KEY"

echo ""
echo "📋 Testing OS Version CRUD..."
echo "  - Listing OS versions..."
buildctl os-version list

echo "  - Creating new OS version..."
OS_ID=$(buildctl os-version create \
  --name "CLI Test OS" \
  --version "1.0" \
  --output json | jq -r '.id')

echo "  - OS version created with ID: $OS_ID"

echo "  - Getting OS version details..."
buildctl os-version get "$OS_ID"

echo "  - Updating OS version..."
buildctl os-version update "$OS_ID" \
  --version "1.1"

echo "  - Deleting OS version (requires admin key)..."
buildctl config set-key "$ADMIN_KEY"
buildctl os-version delete "$OS_ID"
buildctl config set-key "$API_KEY"

echo ""
echo "📋 Testing Image Type CRUD..."
echo "  - Listing image types..."
buildctl image-type list

echo "  - Creating new image type..."
IMAGE_ID=$(buildctl image-type create \
  --name "CLI Test Image" \
  --description "Test image from CLI" \
  --output json | jq -r '.id')

echo "  - Image type created with ID: $IMAGE_ID"

echo "  - Getting image type details..."
buildctl image-type get "$IMAGE_ID"

echo "  - Updating image type..."
buildctl image-type update "$IMAGE_ID" \
  --description "Updated description"

echo "  - Deleting image type (requires admin key)..."
buildctl config set-key "$ADMIN_KEY"
buildctl image-type delete "$IMAGE_ID"

echo ""
echo "✅ Testing read-only access..."
buildctl config set-key "$READONLY_KEY"

echo "  - Read-only user can list platforms:"
buildctl platform list | head -5

echo "  - Read-only user cannot create (should fail):"
buildctl platform create \
  --name "Should Fail" \
  --cloud-provider "test" \
  --region "test" || echo "✅ Expected failure: write permission required"

echo ""
echo "✅ All CLI tests completed successfully!"
