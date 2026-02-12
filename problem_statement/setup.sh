#!/bin/bash
# State-Based Build Framework Setup Script
# Copies the framework to a new workspace

set -e

if [ $# -eq 0 ] || [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "State-Based Build Framework Setup Script"
    echo ""
    echo "Usage: $0 <target-directory>"
    echo ""
    echo "This script copies the complete State-Based Build Framework"
    echo "to a new workspace directory for implementing resumable"
    echo "multi-cloud IaaS image builds."
    echo ""
    echo "Example:"
    echo "  $0 /path/to/new/image-build-project"
    echo ""
    echo "The framework includes:"
    echo "  - State code system (0-100 by 5s)"
    echo "  - Failure handling and retry logic"
    echo "  - Storage implementations (SQLite, cloud)"
    echo "  - Sample AWS RHEL 8 implementation"
    echo "  - Packer, Ansible, and Concourse integration"
    exit 0
fi

TARGET_DIR="$1"

if [ ! -d "$TARGET_DIR" ]; then
    echo "Creating target directory: $TARGET_DIR"
    mkdir -p "$TARGET_DIR"
fi

echo "Copying State-Based Build Framework to: $TARGET_DIR"

# Copy the framework
cp -r .copilot/ "$TARGET_DIR/"

echo "Framework copied successfully!"
echo ""
echo "Next steps:"
echo "1. cd $TARGET_DIR"
echo "2. cat .copilot/README.md (to understand the framework)"
echo "3. cat .copilot/sample-implementation.md (for concrete examples)"
echo "4. Start implementing based on your cloud provider and image type"
echo ""
echo "Happy building! 🚀"