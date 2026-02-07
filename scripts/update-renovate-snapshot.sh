#!/bin/bash

# Update Renovate Snapshot Script
# This script generates snapshots automatically and can validate them

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SNAPSHOT_FILE="$REPO_ROOT/.github/renovate-snapshot.yaml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

show_help() {
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  --check      Check if snapshot is valid (CI mode)"
    echo "  --update     Update snapshot from Renovate output"
    echo "  --summary    Show current snapshot summary"
    echo "  --help       Show this help"
}

check_snapshot() {
    echo -e "${BLUE}🔍 Checking Renovate snapshot...${NC}"
    
    if [ ! -f "$SNAPSHOT_FILE" ]; then
        echo -e "${RED}❌ Snapshot file not found: $SNAPSHOT_FILE${NC}"
        exit 1
    fi
    
    # Check if YAML is valid
    if ! python3 -c "import yaml; yaml.safe_load(open('$SNAPSHOT_FILE'))" 2>/dev/null; then
        echo -e "${RED}❌ Invalid YAML format in snapshot${NC}"
        exit 1
    fi
    
    # Count dependencies dynamically by counting dependency entries
    TOTAL_DEPS=$(python3 -c "
import yaml
with open('$SNAPSHOT_FILE') as f:
    data = yaml.safe_load(f)
    count = 0
    for group in data.get('dependency_groups', {}).values():
        count += len(group)
    print(count)
" 2>/dev/null || echo "0")
    
    echo -e "${GREEN}✅ Snapshot is valid${NC}"
    echo -e "${GREEN}📊 Total dependencies: $TOTAL_DEPS${NC}"
}

generate_snapshot() {
    echo -e "${BLUE}🔄 Generating Renovate snapshot from Renovate output...${NC}"
    
    # Run Renovate to get current dependencies
    echo "Running Renovate to extract dependencies..."
    
    if ! docker run --rm -e LOG_LEVEL=debug -v "$REPO_ROOT":/workspace -w /workspace renovate/renovate --platform=local --dry-run 2>/tmp/renovate_errors.txt > /tmp/renovate_full.txt; then
        echo -e "${RED}❌ Failed to run Renovate${NC}"
        exit 1
    fi
    
    echo -e "${YELLOW}📊 Parsing Renovate output...${NC}"
    
    # Extract the JSON section from the output - try to get complete JSON
    if ! grep -A 10000 "DEBUG: packageFiles with updates" /tmp/renovate_full.txt | sed '1d' > /tmp/renovate_output.txt; then
        echo -e "${RED}❌ Failed to extract package files section from Renovate output${NC}"
        exit 1
    fi
    
    # Check if we got any output
    if [ ! -s /tmp/renovate_output.txt ]; then
        echo -e "${RED}❌ No dependency data extracted from Renovate${NC}"
        exit 1
    fi
    
    # Run the Python script to generate snapshot
    if ! python3 "$SCRIPT_DIR/update-renovate-snapshot.py" /tmp/renovate_output.txt "$SNAPSHOT_FILE"; then
        echo -e "${RED}❌ Failed to generate snapshot${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Snapshot generated automatically from Renovate!${NC}"
    echo -e "${GREEN}📄 Snapshot file: $SNAPSHOT_FILE${NC}"
    
    # Cleanup temporary files
    rm -f /tmp/renovate_output.txt /tmp/renovate_full.txt /tmp/renovate_errors.txt
}

show_summary() {
    echo -e "${BLUE}📊 Renovate Snapshot Summary${NC}"
    echo ""
    
    if [ ! -f "$SNAPSHOT_FILE" ]; then
        echo -e "${RED}❌ Snapshot file not found: $SNAPSHOT_FILE${NC}"
        exit 1
    fi
    
    # Count dependencies dynamically
    local snapshot_file="$SNAPSHOT_FILE"
    TOTAL_DEPS=$(python3 -c "
import yaml
with open(\"$(echo '$snapshot_file')\") as f:
    data = yaml.safe_load(f)
    count = sum(len(group) for group in data.get('dependency_groups', {}).values())
    print(count)
" 2>/dev/null || echo "0")
    
    echo -e "${GREEN}Total Dependencies: $TOTAL_DEPS${NC}"
    echo ""
    echo -e "${YELLOW}📋 Dependency Groups:${NC}"
    
    # Show groups using simple grep
    echo -e "${YELLOW}  Docker Images: $(grep -c 'Docker Images:' \"$SNAPSHOT_FILE\" || echo '0')${NC}"
    echo -e "${YELLOW}  GitHub Releases: $(grep -c 'GitHub Releases:' \"$SNAPSHOT_FILE\" || echo '0')${NC}"
    echo -e "${YELLOW}  Git References: $(grep -c 'Git References:' \"$SNAPSHOT_FILE\" || echo '0')${NC}"
}

# Main script logic
case "${1:-}" in
    --help|-h)
        show_help
        ;;
    --check|--ci)
        check_snapshot
        ;;
    --summary|-s)
        show_summary
        ;;
    --update|-u)
        generate_snapshot
        ;;
    "")
        echo -e "${YELLOW}No option specified. Use --help for usage.${NC}"
        exit 1
        ;;
    *)
        echo -e "${RED}Unknown option: $1${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac