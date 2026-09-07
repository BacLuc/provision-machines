#!/bin/bash

# Docker Volume and Network Cleanup Script
# Removes tracked volumes and networks that are idle beyond the age threshold.
# NEVER deletes untracked items (missing metadata = skip, not delete).
# Mirrors docker-cleanup.sh style: DRY_RUN, AGE_THRESHOLD_DAYS, color output, summary.

set -euo pipefail

# Thresholds
AGE_THRESHOLD_DAYS=${AGE_THRESHOLD_DAYS:-60}
DRY_RUN=${DRY_RUN:-true}

# Directories for metadata (written by docker-events-track.sh)
VOLUME_USAGE_DIR="${HOME}/.local/share/docker-volume-usage"
NETWORK_USAGE_DIR="${HOME}/.local/share/docker-network-usage"

# Allow override for root-run cleanup scripts (cleanup-script.sh runs as root)
CLEANUP_USER="${CLEANUP_USER:-}"
if [ -n "${CLEANUP_USER:-}" ]; then
  HOME_BASE="/home/${CLEANUP_USER}"
  VOLUME_USAGE_DIR="${HOME_BASE}/.local/share/docker-volume-usage"
  NETWORK_USAGE_DIR="${HOME_BASE}/.local/share/docker-network-usage"
fi

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

CURRENT_TIME=$(date +%s)

deleted_count=0
would_delete_count=0
kept_count=0
skipped_count=0

# --- Volumes ---
echo -e "${GREEN}Starting Docker Volume Cleanup...${NC}"
echo "Volumes must be tracked (have metadata) AND idle > ${AGE_THRESHOLD_DAYS} days to be deleted."
echo ""

if [ -d "$VOLUME_USAGE_DIR" ]; then
  for metadata_file in "${VOLUME_USAGE_DIR}"/*.json; do
    [ -f "$metadata_file" ] || continue

    vol_name=$(jq -r '.name // empty' "$metadata_file" 2>/dev/null)
    last_used=$(jq -r '.last_used // 0' "$metadata_file" 2>/dev/null)

    [ -z "$vol_name" ] && continue
    # Skip anonymous volumes (64-hex chars, no slashes — just skip for safety)
    echo "$vol_name" | grep -qE '^[0-9a-f]{64}$' && { echo -e "${YELLOW}[SKIP]${NC} $vol_name (anonymous volume)"; skipped_count=$((skipped_count + 1)); continue; }
    # Skip anything that looks like a local-path or k8s-style volume
    echo "$vol_name" | grep -qE '(local-path|k8s)' && { echo -e "${YELLOW}[SKIP]${NC} $vol_name (local-path/k8s volume)"; skipped_count=$((skipped_count + 1)); continue; }

    # Check age
    if [ "$last_used" = "0" ]; then
      echo -e "${YELLOW}[KEEP]${NC} $vol_name — no timestamp in metadata"
      kept_count=$((kept_count + 1))
      continue
    fi
    age_seconds=$((CURRENT_TIME - last_used))
    age_days=$((age_seconds / 86400))
    if [ "$age_days" -lt "$AGE_THRESHOLD_DAYS" ]; then
      echo -e "${YELLOW}[KEEP]${NC} $vol_name — only ${age_days} days old (< ${AGE_THRESHOLD_DAYS})"
      kept_count=$((kept_count + 1))
      continue
    fi

    # Check if any container references this volume (running or stopped)
    containers=$(docker ps -a --filter "volume=${vol_name}" --format "{{.Names}}" 2>/dev/null || true)
    if [ -n "$containers" ]; then
      echo -e "${YELLOW}[KEEP]${NC} $vol_name — referenced by containers: $containers"
      kept_count=$((kept_count + 1))
      continue
    fi

    # Safe to delete
    would_delete_count=$((would_delete_count + 1))
    if [ "$DRY_RUN" = "true" ]; then
      echo -e "${RED}[DELETE]${NC} $vol_name — idle ${age_days} days, no container references (dry run)"
    else
      echo -e "${RED}[DELETE]${NC} $vol_name — idle ${age_days} days, no container references"
      if docker volume rm "$vol_name" > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓ Deleted${NC}"
        rm -f "$metadata_file"
        deleted_count=$((deleted_count + 1))
      else
        echo -e "  ${YELLOW}⚠ Failed to delete (may be in use)${NC}"
      fi
    fi
  done
else
  echo "No volume metadata directory found at ${VOLUME_USAGE_DIR}"
fi

echo ""

# --- Networks ---
echo -e "${GREEN}Starting Docker Network Cleanup...${NC}"
echo "Networks must be tracked (have metadata), idle > ${AGE_THRESHOLD_DAYS} days, and not in use."
echo ""

# Built-in networks that must never be deleted
BUILTIN_NETWORKS="bridge host none"

if [ -d "$NETWORK_USAGE_DIR" ]; then
  for metadata_file in "${NETWORK_USAGE_DIR}"/*.json; do
    [ -f "$metadata_file" ] || continue

    net_name=$(jq -r '.name // empty' "$metadata_file" 2>/dev/null)
    last_used=$(jq -r '.last_used // 0' "$metadata_file" 2>/dev/null)

    [ -z "$net_name" ] && continue

    # Skip built-in networks
    is_builtin=false
    for builtin in $BUILTIN_NETWORKS; do
      if [ "$net_name" = "$builtin" ]; then
        is_builtin=true
        break
      fi
    done
    if [ "$is_builtin" = true ]; then
      echo -e "${YELLOW}[SKIP]${NC} $net_name (built-in network)"
      skipped_count=$((skipped_count + 1))
      continue
    fi

    # Skip docker-compose networks
    labels=$(docker network inspect "$net_name" --format '{{index .Labels "com.docker.compose.project"}}' 2>/dev/null || true)
    if [ -n "$labels" ]; then
      echo -e "${YELLOW}[SKIP]${NC} $net_name (docker-compose network: $labels)"
      skipped_count=$((skipped_count + 1))
      continue
    fi

    # Check age
    if [ "$last_used" = "0" ]; then
      echo -e "${YELLOW}[KEEP]${NC} $net_name — no timestamp in metadata"
      kept_count=$((kept_count + 1))
      continue
    fi
    age_seconds=$((CURRENT_TIME - last_used))
    age_days=$((age_seconds / 86400))
    if [ "$age_days" -lt "$AGE_THRESHOLD_DAYS" ]; then
      echo -e "${YELLOW}[KEEP]${NC} $net_name — only ${age_days} days old (< ${AGE_THRESHOLD_DAYS})"
      kept_count=$((kept_count + 1))
      continue
    fi

    # Check if any container is connected to this network
    containers=$(docker network inspect "$net_name" --format '{{range $k, $v := .Containers}}{{$v.Name}} {{end}}' 2>/dev/null || true)
    if [ -n "$containers" ]; then
      echo -e "${YELLOW}[KEEP]${NC} $net_name — connected containers: $containers"
      kept_count=$((kept_count + 1))
      continue
    fi

    # Safe to delete
    would_delete_count=$((would_delete_count + 1))
    if [ "$DRY_RUN" = "true" ]; then
      echo -e "${RED}[DELETE]${NC} $net_name — idle ${age_days} days, no container connections (dry run)"
    else
      echo -e "${RED}[DELETE]${NC} $net_name — idle ${age_days} days, no container connections"
      if docker network rm "$net_name" > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓ Deleted${NC}"
        rm -f "$metadata_file"
        deleted_count=$((deleted_count + 1))
      else
        echo -e "  ${YELLOW}⚠ Failed to delete (may be in use)${NC}"
      fi
    fi
  done
else
  echo "No network metadata directory found at ${NETWORK_USAGE_DIR}"
fi

echo ""
echo -e "${GREEN}Docker volume/network cleanup complete!${NC}"
echo "Summary: deleted=$deleted_count would_delete=$would_delete_count kept=$kept_count skipped=$skipped_count"
