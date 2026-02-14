#!/usr/bin/env bash
#
# Semantic Versioning Helper Script
# Manages version numbers for the Build State project
#
# Usage:
#   ./scripts/version.sh current              # Show current version
#   ./scripts/version.sh bump major|minor|patch  # Bump version
#   ./scripts/version.sh set <version>        # Set specific version
#   ./scripts/version.sh tag                  # Create git tag for current version
#   ./scripts/version.sh full                 # Get version with git info

set -euo pipefail

VERSION_FILE="VERSION"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

# Read current version
get_version() {
    if [[ -f "$VERSION_FILE" ]]; then
        cat "$VERSION_FILE"
    else
        echo "0.0.0"
    fi
}

# Write version to file
set_version() {
    local version="$1"
    echo "$version" > "$VERSION_FILE"
    echo "Version set to $version"
}

# Parse version into components
parse_version() {
    local version="$1"
    local regex="^([0-9]+)\.([0-9]+)\.([0-9]+)(-.*)?$"
    
    if [[ $version =~ $regex ]]; then
        MAJOR="${BASH_REMATCH[1]}"
        MINOR="${BASH_REMATCH[2]}"
        PATCH="${BASH_REMATCH[3]}"
        PRERELEASE="${BASH_REMATCH[4]}"
    else
        echo "Error: Invalid version format: $version" >&2
        return 1
    fi
}

# Bump version
bump_version() {
    local bump_type="$1"
    local current_version
    current_version=$(get_version)
    
    parse_version "$current_version"
    
    case "$bump_type" in
        major)
            MAJOR=$((MAJOR + 1))
            MINOR=0
            PATCH=0
            ;;
        minor)
            MINOR=$((MINOR + 1))
            PATCH=0
            ;;
        patch)
            PATCH=$((PATCH + 1))
            ;;
        *)
            echo "Error: Invalid bump type. Use: major, minor, or patch" >&2
            return 1
            ;;
    esac
    
    local new_version="${MAJOR}.${MINOR}.${PATCH}"
    set_version "$new_version"
    echo "$new_version"
}

# Get full version with git info
get_full_version() {
    local version
    version=$(get_version)
    local git_sha
    local git_branch
    local git_dirty=""
    
    if git rev-parse --git-dir > /dev/null 2>&1; then
        git_sha=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
        git_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
        
        # Check if working directory is dirty
        if ! git diff-index --quiet HEAD -- 2>/dev/null; then
            git_dirty="-dirty"
        fi
        
        echo "${version}+${git_sha}${git_dirty}"
    else
        echo "$version"
    fi
}

# Create git tag
create_tag() {
    local version
    version=$(get_version)
    local tag="v${version}"
    
    if git rev-parse "$tag" >/dev/null 2>&1; then
        echo "Tag $tag already exists" >&2
        return 1
    fi
    
    git tag -a "$tag" -m "Release version $version"
    echo "Created tag: $tag"
    echo "Push with: git push origin $tag"
}

# Get next version based on conventional commits
get_next_version() {
    local current_version
    current_version=$(get_version)
    
    parse_version "$current_version"
    
    # Get commits since last tag
    local last_tag
    last_tag=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
    
    if [[ -z "$last_tag" ]]; then
        # No tags yet, start from current version
        echo "$current_version"
        return
    fi
    
    # Check commit messages for conventional commit types
    local commits
    commits=$(git log "${last_tag}..HEAD" --pretty=format:"%s" 2>/dev/null || echo "")
    
    local bump_type="patch"
    
    if echo "$commits" | grep -q "^feat!:" || echo "$commits" | grep -q "BREAKING CHANGE:"; then
        bump_type="major"
    elif echo "$commits" | grep -q "^feat:"; then
        bump_type="minor"
    elif echo "$commits" | grep -q "^fix:"; then
        bump_type="patch"
    fi
    
    case "$bump_type" in
        major)
            MAJOR=$((MAJOR + 1))
            MINOR=0
            PATCH=0
            ;;
        minor)
            MINOR=$((MINOR + 1))
            PATCH=0
            ;;
        patch)
            PATCH=$((PATCH + 1))
            ;;
    esac
    
    echo "${MAJOR}.${MINOR}.${PATCH}"
}

# Main command handler
main() {
    local command="${1:-current}"
    
    case "$command" in
        current)
            get_version
            ;;
        full)
            get_full_version
            ;;
        bump)
            if [[ $# -lt 2 ]]; then
                echo "Error: bump requires type (major|minor|patch)" >&2
                exit 1
            fi
            bump_version "$2"
            ;;
        set)
            if [[ $# -lt 2 ]]; then
                echo "Error: set requires version number" >&2
                exit 1
            fi
            set_version "$2"
            ;;
        tag)
            create_tag
            ;;
        next)
            get_next_version
            ;;
        help|--help|-h)
            cat <<EOF
Semantic Versioning Helper

Usage:
  $0 current              Show current version
  $0 full                 Show version with git info
  $0 bump major|minor|patch  Bump version
  $0 set <version>        Set specific version
  $0 tag                  Create git tag for current version
  $0 next                 Calculate next version from commits
  $0 help                 Show this help message

Examples:
  $0 current              # Output: 2.0.0
  $0 full                 # Output: 2.0.0+abc1234
  $0 bump patch           # Bumps to 2.0.1
  $0 set 3.0.0-beta.1     # Sets version to 3.0.0-beta.1
  $0 tag                  # Creates git tag v2.0.0
EOF
            ;;
        *)
            echo "Error: Unknown command: $command" >&2
            echo "Run '$0 help' for usage information" >&2
            exit 1
            ;;
    esac
}

main "$@"
