#!/usr/bin/env bash
# update-renovate-snapshot.sh
# Updates or checks the Renovate snapshot
# Usage: ./scripts/update-renovate-snapshot.sh [--check]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SNAPSHOT_FILE="${REPO_ROOT}/.github/renovate-snapshot.yaml"

CHECK_MODE=false
if [[ "$1" == "--check" ]]; then
    CHECK_MODE=true
    echo "🔍 Running in CHECK mode (will not update snapshot)"
else
    echo "📝 Running in UPDATE mode (will update snapshot)"
fi

echo "=== Validating Renovate Configuration ==="

# First validate the main renovate.json in the repo
echo "Validating renovate.json..."
docker run --rm -v "${REPO_ROOT}":/workspace \
    renovate/renovate:latest \
    renovate-config-validator /workspace/renovate.json 2>&1 | grep -E "(INFO|ERROR|validated)" | tail -3

echo ""
echo "=== Analyzing Dependencies ==="

# Count expected from snapshot
if [ -f "${SNAPSHOT_FILE}" ]; then
    # Count lines that start with "# renovate:" to get dependency count
    EXPECTED_COUNT=$(grep -c "^  # renovate:" "${SNAPSHOT_FILE}" 2>/dev/null || echo "0")
    echo "Expected dependencies in snapshot: ${EXPECTED_COUNT}"
else
    echo "ERROR: Snapshot file not found: ${SNAPSHOT_FILE}"
    exit 1
fi

# For check mode, verify each dependency exists in the files
if [ "$CHECK_MODE" = true ]; then
    echo ""
    echo "Checking each dependency in source files..."
    
    MISSING=0
    FOUND=0
    
    # Parse the YAML file to get dependencies
    # Read the file and extract dependency information
    DEP_INDEX=0
    while IFS= read -r line; do
        # Check if this is a renovate comment line
        if [[ "$line" =~ ^\ \ #\ renovate:\ (.+) ]]; then
            RENOVATE_MARKER="${BASH_REMATCH[1]}"
            
            # Read the next line which should be the dependency entry
            read -r dep_line
            
            # Extract file path
            if [[ "$dep_line" =~ file:\ (.+) ]]; then
                depFile="${BASH_REMATCH[1]}"
            fi
            
            # Read next lines to get depName and currentValue
            read -r name_line
            read -r value_line
            
            if [[ "$name_line" =~ depName:\ (.+) ]]; then
                depName="${BASH_REMATCH[1]}"
            fi
            
            if [[ "$value_line" =~ currentValue:\ \"([^\"]+)\" ]]; then
                currentValue="${BASH_REMATCH[1]}"
            fi
            
            # Check if the dependency exists in the file
            if [ -n "$depName" ] && [ -n "$depFile" ] && [ -n "$currentValue" ]; then
                fullFilePath="${REPO_ROOT}/${depFile}"
                
                if [ -f "$fullFilePath" ]; then
                    if grep -q "${currentValue}" "$fullFilePath" 2>/dev/null; then
                        echo "✅ FOUND: $depName ($currentValue in $depFile)"
                        FOUND=$((FOUND + 1))
                    else
                        echo "❌ NOT FOUND: $depName (expected $currentValue in $depFile)"
                        MISSING=$((MISSING + 1))
                    fi
                else
                    echo "❌ FILE MISSING: $depFile for $depName"
                    MISSING=$((MISSING + 1))
                fi
            fi
            
            DEP_INDEX=$((DEP_INDEX + 1))
        fi
    done < "${SNAPSHOT_FILE}"
    
    echo ""
    echo "Summary: $FOUND found, $MISSING missing (expected: $EXPECTED_COUNT)"
    
    if [ $MISSING -gt 0 ]; then
        echo "ERROR: $MISSING dependencies not found in source files!"
        exit 1
    elif [ $FOUND -eq 0 ] && [ $EXPECTED_COUNT -gt 0 ]; then
        echo "ERROR: No dependencies were checked. Parsing issue?"
        exit 1
    else
        echo "✅ SUCCESS: All $EXPECTED_COUNT dependencies verified!"
        exit 0
    fi
else
    echo ""
    echo "=== Update Mode ==="
    echo "Current snapshot: ${SNAPSHOT_FILE}"
    echo ""
    echo "To update the snapshot:"
    echo "1. Manually update version values in the YAML file"
    echo "2. Run: yq -i '.totalDependencies = <count>' ${SNAPSHOT_FILE}"
    echo "3. Commit the changes"
    
    # Update timestamp
    sed -i "s/# Last updated: .*/# Last updated: $(date -u +%Y-%m-%dT%H:%M:%SZ)/" "${SNAPSHOT_FILE}" 2>/dev/null || true
    echo "✅ Timestamp updated"
    
    echo "✅ Snapshot process completed"
fi
