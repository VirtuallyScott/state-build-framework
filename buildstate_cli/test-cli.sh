#!/bin/bash

# Test script for BuildState CLI
# Validates the CLI installation and basic functionality

set -e

echo "🧪 Testing BuildState CLI"
echo "========================="

# Check if CLI is installed
if ! command -v buildctl &> /dev/null; then
    echo "❌ buildctl command not found. Installing in development mode..."
    cd /Users/scottsmith/tmp/state-builds/buildstate_cli
    pip install -e .
fi

echo "✅ CLI is available"

# Test help
echo ""
echo "📚 Testing help command..."
buildctl --help | head -10

# Test config commands
echo ""
echo "⚙️  Testing config commands..."
buildctl config --help | head -5

# Test build commands
echo ""
echo "🏗️  Testing build commands..."
buildctl build --help | head -5

# Test state commands
echo ""
echo "🔄 Testing state commands..."
buildctl state --help | head -5

# Test dashboard commands
echo ""
echo "📊 Testing dashboard commands..."
buildctl dashboard --help | head -5

echo ""
echo "🎉 CLI structure validation complete!"
echo ""
echo "💡 Next steps:"
echo "1. Start the API service: cd ../api_service && make up"
echo "2. Configure CLI: buildctl config set-url http://localhost:8080"
echo "3. Set API key: buildctl auth set-key dev-key-12345"
echo "4. Test full integration: buildctl health"