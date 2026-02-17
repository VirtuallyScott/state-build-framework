#!/usr/bin/env bash
#
# GitHub Actions Status Checker
# Monitors GitHub Actions workflow runs
#
# Usage:
#   ./scripts/gh-actions-status.sh                 # Show recent runs
#   ./scripts/gh-actions-status.sh watch           # Watch most recent run
#   ./scripts/gh-actions-status.sh workflow <name> # Show specific workflow
#   ./scripts/gh-actions-status.sh logs <run-id>   # Show logs for run

set -euo pipefail

# Check if gh CLI is available
if ! command -v gh &> /dev/null; then
    echo "Error: GitHub CLI (gh) is not installed" >&2
    echo "Install from: https://cli.github.com/" >&2
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo "Error: Not authenticated with GitHub CLI" >&2
    echo "Run: gh auth login" >&2
    exit 1
fi

COMMAND="${1:-list}"

case "$COMMAND" in
    list|ls)
        echo "=== Recent GitHub Actions Runs ==="
        gh run list --limit 10
        ;;
    
    watch|w)
        RUN_ID="${2:-}"
        if [[ -z "$RUN_ID" ]]; then
            echo "Watching most recent workflow run..."
            gh run watch
        else
            echo "Watching run #$RUN_ID..."
            gh run watch "$RUN_ID"
        fi
        ;;
    
    workflow|wf)
        if [[ $# -lt 2 ]]; then
            echo "Error: workflow name required" >&2
            echo "Usage: $0 workflow <workflow-name>" >&2
            echo "" >&2
            echo "Available workflows:" >&2
            gh workflow list
            exit 1
        fi
        WORKFLOW="$2"
        echo "=== Runs for workflow: $WORKFLOW ==="
        gh run list --workflow="$WORKFLOW" --limit 10
        ;;
    
    view|v)
        if [[ $# -lt 2 ]]; then
            echo "Error: run ID required" >&2
            echo "Usage: $0 view <run-id>" >&2
            exit 1
        fi
        RUN_ID="$2"
        gh run view "$RUN_ID"
        ;;
    
    logs|l)
        if [[ $# -lt 2 ]]; then
            echo "Error: run ID required" >&2
            echo "Usage: $0 logs <run-id>" >&2
            exit 1
        fi
        RUN_ID="$2"
        gh run view "$RUN_ID" --log
        ;;
    
    rerun|r)
        if [[ $# -lt 2 ]]; then
            echo "Error: run ID required" >&2
            echo "Usage: $0 rerun <run-id>" >&2
            exit 1
        fi
        RUN_ID="$2"
        echo "Rerunning workflow run #$RUN_ID..."
        gh run rerun "$RUN_ID"
        ;;
    
    cancel|c)
        if [[ $# -lt 2 ]]; then
            echo "Error: run ID required" >&2
            echo "Usage: $0 cancel <run-id>" >&2
            exit 1
        fi
        RUN_ID="$2"
        echo "Cancelling workflow run #$RUN_ID..."
        gh run cancel "$RUN_ID"
        ;;
    
    workflows)
        echo "=== Available Workflows ==="
        gh workflow list
        ;;
    
    trigger|t)
        if [[ $# -lt 2 ]]; then
            echo "Error: workflow name required" >&2
            echo "Usage: $0 trigger <workflow-name>" >&2
            echo "" >&2
            echo "Available workflows:" >&2
            gh workflow list
            exit 1
        fi
        WORKFLOW="$2"
        echo "Triggering workflow: $WORKFLOW"
        gh workflow run "$WORKFLOW"
        echo "Workflow triggered! Check status with: $0 list"
        ;;
    
    summary|s)
        echo "=== Workflow Summary ==="
        echo ""
        echo "Recent Runs:"
        gh run list --limit 5
        echo ""
        echo "---"
        echo ""
        echo "Available Workflows:"
        gh workflow list
        echo ""
        echo "---"
        echo ""
        echo "Use '$0 help' for more commands"
        ;;
    
    help|h|--help)
        cat <<EOF
GitHub Actions Status Checker

Usage:
  $0 <command> [arguments]

Commands:
  list, ls                    List recent workflow runs
  watch, w [run-id]           Watch workflow run (default: most recent)
  workflow, wf <name>         List runs for specific workflow
  view, v <run-id>            View details of a workflow run
  logs, l <run-id>            View logs for a workflow run
  rerun, r <run-id>           Rerun a failed workflow
  cancel, c <run-id>          Cancel a running workflow
  workflows                   List all workflows
  trigger, t <workflow>       Manually trigger a workflow
  summary, s                  Show summary of workflows and runs
  help, h                     Show this help message

Examples:
  $0 list                                  # Show recent runs
  $0 watch                                 # Watch most recent run
  $0 workflow build-and-publish.yml        # Show build workflow runs
  $0 view 12345678                         # View run details
  $0 logs 12345678                         # Show run logs
  $0 trigger build-and-publish.yml         # Manually trigger build
  $0 rerun 12345678                        # Rerun failed workflow

Workflows in this project:
  - build-and-publish.yml       Build and publish containers
  - version-and-release.yml     Bump version and create releases
  - test.yml                    Run tests and linting

For more information:
  gh run --help
  gh workflow --help
EOF
        ;;
    
    *)
        echo "Error: Unknown command: $COMMAND" >&2
        echo "Run '$0 help' for usage information" >&2
        exit 1
        ;;
esac
