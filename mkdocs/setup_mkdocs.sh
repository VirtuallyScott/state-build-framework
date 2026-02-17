#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
IMAGE_NAME="mkdocs-state-builds"

build_docker() {
    echo "Building Docker image..."
    docker build -t "$IMAGE_NAME" "$SCRIPT_DIR"
}

build_site() {
    echo "Building MkDocs site..."
    docker run --rm -v "$SCRIPT_DIR:/home/docsuser/docs" "$IMAGE_NAME" mkdocs build
}

publish() {
    echo "Publishing to gh-pages..."
    # Check if mkdocs is installed on host
    if ! command -v mkdocs &> /dev/null; then
        echo "mkdocs not found on host. Installing in virtual environment..."
        cd "$SCRIPT_DIR"
        if [ ! -d "venv" ]; then
            python3 -m venv venv
        fi
        source venv/bin/activate
        pip install -r requirements.txt
    fi
    
    echo "Deploying to GitHub Pages..."
    cd "$SCRIPT_DIR"
    mkdocs gh-deploy --force
    echo "Published to gh-pages!"
}

serve() {
    echo "Starting local dev server at http://localhost:8000..."
    docker run --rm -it -p 8000:8000 -v "$SCRIPT_DIR:/home/docsuser/docs" "$IMAGE_NAME"
}

print_usage() {
    cat <<EOF
Usage: $0 [command]

Commands:
    build       Build Docker image and MkDocs site
    publish     Build and publish to GitHub Pages
    serve       Start local development server
    help        Show this help message

If no command is given, 'publish' is run by default.
EOF
}

main() {
    cd "$SCRIPT_DIR"
    
    case "${1:-publish}" in
        build)
            build_docker
            build_site
            ;;
        publish)
            build_docker
            build_site
            publish
            ;;
        serve)
            build_docker
            serve
            ;;
        help|--help|-h)
            print_usage
            ;;
        *)
            echo "Unknown command: $1"
            print_usage
            exit 1
            ;;
    esac
}

main "$@"
