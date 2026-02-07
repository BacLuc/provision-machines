#!/bin/bash

# Update Renovate Snapshot Script
# This script generates snapshots automatically and can validate them

set -euo pipefail

SCRIPT_DIR=$(realpath $(dirname $0))
REPO_ROOT=$(dirname $SCRIPT_DIR)
SNAPSHOT_FILE="$REPO_ROOT/.github/renovate-snapshot.json"

show_help() {
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  --check      Check if snapshot is valid (CI mode)"
    echo "  --update     Update snapshot from Renovate output"
    echo "  --help       Show this help"
}

check_snapshot() {
    generate_snapshot > $SNAPSHOT_FILE
    git diff --exit-code $SNAPSHOT_FILE
}

generate_snapshot() {
    docker run --rm -e LOG_LEVEL=info -e LOG_FORMAT=json -v $PWD:/workspace -w /workspace renovate/renovate --platform=local 2>/tmp/renovate-err.log | jq 'select(.level==40) | .githubDeps'
}

# Main script logic
case "${1:-}" in
    --help|-h)
        show_help
        ;;
    --check|--ci)
        check_snapshot
        exit $?
        ;;
    --update|-u)
        generate_snapshot > $SNAPSHOT_FILE
        ;;
    "")
        echo -e "No option specified. Use --help for usage."
        exit 1
        ;;
    *)
        echo -e "Unknown option: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
