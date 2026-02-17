#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

setup_venv() {
    if [ ! -d "$VENV_DIR" ]; then
        echo "Creating Python virtual environment..."
        python3 -m venv "$VENV_DIR"
    fi
    
    echo "Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
    
    # Check if dependencies are installed
    if ! pip show mkdocs-material &> /dev/null; then
        echo "Installing dependencies..."
        pip install --upgrade pip
        pip install -r "$SCRIPT_DIR/requirements.txt"
    fi
}

build() {
    echo "Building MkDocs site..."
    setup_venv
    cd "$SCRIPT_DIR"
    mkdocs build --clean
    echo "Site built successfully in $SCRIPT_DIR/site/"
}

publish() {
    echo "Publishing to GitHub Pages..."
    setup_venv
    cd "$SCRIPT_DIR"
    mkdocs gh-deploy --clean --force
    echo "✅ Published to https://VirtuallyScott.github.io/state-build-framework/"
}

serve() {
    echo "Starting local dev server at http://127.0.0.1:8000..."
    setup_venv
    cd "$SCRIPT_DIR"
    mkdocs serve
}

clean() {
    echo "Cleaning build artifacts..."
    rm -rf "$SCRIPT_DIR/site"
    echo "Cleaned site/ directory"
}

print_usage() {
    cat <<EOF
Usage: $0 [command]

Commands:
    build       Build the MkDocs site locally
    publish     Build and publish to GitHub Pages
    serve       Start local development server (default: http://127.0.0.1:8000)
    clean       Remove build artifacts
    help        Show this help message

If no command is given, 'serve' is run by default for development.
EOF
}

main() {
    cd "$SCRIPT_DIR"
    
    case "${1:-serve}" in
        build)
            build
            ;;
        publish)
            publish
            ;;
        serve)
            serve
            ;;
        clean)
            clean
            ;;
        help|--help|-h)
            print_usage
            ;;
        *)
            echo "❌ Unknown command: $1"
            print_usage
            exit 1
            ;;
    esac
}

main "$@"
