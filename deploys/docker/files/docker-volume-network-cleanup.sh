#!/bin/bash

set -euo pipefail

AGE_THRESHOLD_DAYS=${AGE_THRESHOLD_DAYS:-60}
case "$AGE_THRESHOLD_DAYS" in
  ''|*[!0-9]*) AGE_THRESHOLD_DAYS=60 ;;
esac
DRY_RUN=${DRY_RUN:-true}

resolve_home() {
  local home_dir=""
  if [ -n "${CLEANUP_HOME:-}" ]; then
    home_dir="$CLEANUP_HOME"
  elif [ -n "${CLEANUP_USER:-}" ]; then
    home_dir=$(getent passwd "$CLEANUP_USER" | cut -d: -f6)
  elif [ -n "${SUDO_USER:-}" ]; then
    home_dir=$(getent passwd "$SUDO_USER" | cut -d: -f6)
  fi
  if [ -z "$home_dir" ]; then
    home_dir="${HOME}"
  fi
  echo "$home_dir"
}

HOME_DIR=$(resolve_home)
VOLUME_USAGE_DIR="${HOME_DIR}/.local/share/docker-volume-usage"
NETWORK_USAGE_DIR="${HOME_DIR}/.local/share/docker-network-usage"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

CURRENT_TIME=$(date +%s)

deleted_count=0
would_delete_count=0
kept_count=0
skipped_count=0

echo -e "${GREEN}Starting Docker Volume Cleanup...${NC}"
echo "Volumes must be tracked (have metadata) AND idle > ${AGE_THRESHOLD_DAYS} days to be deleted."
echo ""

if [ -d "$VOLUME_USAGE_DIR" ]; then
  for metadata_file in "${VOLUME_USAGE_DIR}"/*.json; do
    [ -f "$metadata_file" ] || continue

    vol_name=$(jq -r '.name // empty' "$metadata_file" 2>/dev/null)
    last_used=$(jq -r '.last_used // 0' "$metadata_file" 2>/dev/null)

    [ -z "$vol_name" ] && continue
    echo "$vol_name" | grep -qE '^[0-9a-f]{64}$' && { echo -e "${YELLOW}[SKIP]${NC} $vol_name (anonymous volume)"; skipped_count=$((skipped_count + 1)); if [ "$DRY_RUN" != "true" ]; then rm -f "$metadata_file"; fi; continue; }
    echo "$vol_name" | grep -qE '(/|kubelet|kubernetes\.io)' && { echo -e "${YELLOW}[SKIP]${NC} $vol_name (local-path/k8s volume)"; skipped_count=$((skipped_count + 1)); if [ "$DRY_RUN" != "true" ]; then rm -f "$metadata_file"; fi; continue; }

    if [ "$last_used" = "0" ]; then
      echo -e "${YELLOW}[KEEP]${NC} $vol_name — no timestamp in metadata"
      kept_count=$((kept_count + 1))
      continue
    fi
    case "$last_used" in
      ''|*[!0-9]*)
        echo -e "${YELLOW}[KEEP]${NC} $vol_name — non-numeric timestamp in metadata"
        kept_count=$((kept_count + 1))
        continue
        ;;
    esac
    age_seconds=$((CURRENT_TIME - last_used))
    age_days=$((age_seconds / 86400))
    if [ "$age_days" -lt "$AGE_THRESHOLD_DAYS" ]; then
      echo -e "${YELLOW}[KEEP]${NC} $vol_name — only ${age_days} days old (< ${AGE_THRESHOLD_DAYS})"
      kept_count=$((kept_count + 1))
      continue
    fi

    containers=$(docker ps -a --filter "volume=${vol_name}" --format "{{.Names}}" 2>/dev/null || true)
    if [ -n "$containers" ]; then
      echo -e "${YELLOW}[KEEP]${NC} $vol_name — referenced by containers: $containers"
      kept_count=$((kept_count + 1))
      continue
    fi

    exists=$(docker volume ls -q --filter "name=^${vol_name}$" 2>/dev/null || true)
    if [ -z "$exists" ]; then
      echo -e "${YELLOW}[SKIP]${NC} $vol_name (no longer exists)"
      skipped_count=$((skipped_count + 1))
      if [ "$DRY_RUN" != "true" ]; then
        rm -f "$metadata_file"
      fi
      continue
    fi

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

BUILTIN_NETWORKS="bridge host none"

echo -e "${GREEN}Starting Docker Network Cleanup...${NC}"
echo "Networks must be tracked (have metadata), idle > ${AGE_THRESHOLD_DAYS} days, and not in use."
echo ""

if [ -d "$NETWORK_USAGE_DIR" ]; then
  for metadata_file in "${NETWORK_USAGE_DIR}"/*.json; do
    [ -f "$metadata_file" ] || continue

    net_name=$(jq -r '.name // empty' "$metadata_file" 2>/dev/null)
    last_used=$(jq -r '.last_used // 0' "$metadata_file" 2>/dev/null)

    [ -z "$net_name" ] && continue

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
      if [ "$DRY_RUN" != "true" ]; then
        rm -f "$metadata_file"
      fi
      continue
    fi

    labels=$(docker network inspect "$net_name" --format '{{index .Labels "com.docker.compose.project"}}' 2>/dev/null || true)
    if [ -n "$labels" ]; then
      echo -e "${YELLOW}[SKIP]${NC} $net_name (docker-compose network: $labels)"
      skipped_count=$((skipped_count + 1))
      if [ "$DRY_RUN" != "true" ]; then
        rm -f "$metadata_file"
      fi
      continue
    fi

    if [ "$last_used" = "0" ]; then
      echo -e "${YELLOW}[KEEP]${NC} $net_name — no timestamp in metadata"
      kept_count=$((kept_count + 1))
      continue
    fi
    case "$last_used" in
      ''|*[!0-9]*)
        echo -e "${YELLOW}[KEEP]${NC} $net_name — non-numeric timestamp in metadata"
        kept_count=$((kept_count + 1))
        continue
        ;;
    esac
    age_seconds=$((CURRENT_TIME - last_used))
    age_days=$((age_seconds / 86400))
    if [ "$age_days" -lt "$AGE_THRESHOLD_DAYS" ]; then
      echo -e "${YELLOW}[KEEP]${NC} $net_name — only ${age_days} days old (< ${AGE_THRESHOLD_DAYS})"
      kept_count=$((kept_count + 1))
      continue
    fi

    containers=$(docker ps -a --filter "network=${net_name}" --format "{{.Names}}" 2>/dev/null || true)
    if [ -n "$containers" ]; then
      echo -e "${YELLOW}[KEEP]${NC} $net_name — referenced by containers: $containers"
      kept_count=$((kept_count + 1))
      continue
    fi

    exists=$(docker network ls -q --filter "name=^${net_name}$" 2>/dev/null || true)
    if [ -z "$exists" ]; then
      echo -e "${YELLOW}[SKIP]${NC} $net_name (no longer exists)"
      skipped_count=$((skipped_count + 1))
      if [ "$DRY_RUN" != "true" ]; then
        rm -f "$metadata_file"
      fi
      continue
    fi

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
