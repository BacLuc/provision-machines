#!/bin/bash

set -euo pipefail

SIZE_THRESHOLD_MB="200"
SIZE_THRESHOLD=$((SIZE_THRESHOLD_MB * 1024 * 1024))
AGE_THRESHOLD_DAYS=60
DRY_RUN=${DRY_RUN:-true}

resolve_home() {
  local home_dir=""
  if [ -n "${CLEANUP_HOME:-}" ]; then
    home_dir="$CLEANUP_HOME"
  elif [ -n "${CLEANUP_USER:-}" ]; then
    home_dir=$(getent passwd "$CLEANUP_USER" 2>/dev/null | cut -d: -f6 || true)
  elif [ -n "${SUDO_USER:-}" ]; then
    home_dir=$(getent passwd "$SUDO_USER" 2>/dev/null | cut -d: -f6 || true)
  fi
  if [ -z "$home_dir" ]; then
    home_dir="${HOME}"
  fi
  echo "$home_dir"
}

HOME_DIR=$(resolve_home)
METADATA_DIR="${HOME_DIR}/.local/share/docker-image-usage"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Starting Docker Image Cleanup...${NC}"
echo "Images must meet both conditions to be deleted:"
echo "  - Size > ${SIZE_THRESHOLD_MB} MB"
echo "  - Not used in the last 2 months (${AGE_THRESHOLD_DAYS} days)"
echo ""

CURRENT_TIME=$(date +%s)

get_last_used() {
  local image="$1"
  local safe_image_name
  safe_image_name=$(echo "$image" | tr '/' '-' | tr ':' '_')
  local metadata_file="${METADATA_DIR}/${safe_image_name}.json"

  if [ -f "$metadata_file" ]; then
    jq -r '.last_used // 0' "$metadata_file" 2>/dev/null || echo "0"
  else
    echo "0"
  fi
}

while IFS= read -r image_info; do
  [ -z "$image_info" ] && continue

  image_id=$(echo "$image_info" | cut -d'|' -f1)
  size_bytes=$(echo "$image_info" | cut -d'|' -f2)
  image_name=$(echo "$image_info" | cut -d'|' -f3)

  size_mb=$((size_bytes / 1024 / 1024))

  last_used=$(get_last_used "$image_name")

  if [ "$size_bytes" -gt "$SIZE_THRESHOLD" ]; then
    size_condition_met=true
  else
    size_condition_met=false
  fi

  if [ -z "$last_used" ] || [ "$last_used" = "0" ]; then
    last_used_from_container=0
    while IFS= read -r cid; do
      [ -z "$cid" ] && continue
      state=$(docker inspect "$cid" --format '{{.State.Status}}' 2>/dev/null || echo "")
      if [ "$state" = "running" ]; then
        finished=$(docker inspect "$cid" --format '{{.State.StartedAt}}' 2>/dev/null || echo "0")
      else
        finished=$(docker inspect "$cid" --format '{{.State.FinishedAt}}' 2>/dev/null || echo "0")
      fi
      if [ -n "$finished" ] && [ "$finished" != "0001-01-01T00:00:00Z" ]; then
        finished_ts=$(date -u -d "$finished" +%s 2>/dev/null || echo "0")
        if [ "$finished_ts" -gt "$last_used_from_container" ]; then
          last_used_from_container=$finished_ts
        fi
      fi
    done < <(docker ps -a --filter "ancestor=$image_name" --format "{{.ID}}" 2>/dev/null)

    if [ "$last_used_from_container" -gt 0 ]; then
      last_used=$last_used_from_container
    else
      created=$(docker inspect "$image_id" --format '{{.Created}}' 2>/dev/null || echo "0")
      if [ "$created" != "0001-01-01T00:00:00Z" ] && [ -n "$created" ]; then
        last_used=$(date -u -d "$created" +%s 2>/dev/null || echo "0")
      else
        last_used="0"
      fi
    fi
  fi

  if [ -z "$last_used" ] || [ "$last_used" = "0" ]; then
    age_condition_met=true
    days_old="Never used / No metadata"
  else
    age_seconds=$((CURRENT_TIME - last_used))
    age_days=$((age_seconds / 86400))

    if [ "$age_days" -ge "$AGE_THRESHOLD_DAYS" ]; then
      age_condition_met=true
    else
      age_condition_met=false
    fi

    days_old="${age_days} days old"
  fi

  if [ "$size_condition_met" = true ] && [ "$age_condition_met" = true ]; then
    echo -e "${RED}[DELETE]${NC} $image_name (ID: $image_id)"
    echo "  Size: ${size_mb} MB ($size_bytes bytes)"
    echo "  Age: $days_old"

    if [[ "$DRY_RUN" != "true" ]]; then
        if docker rmi "$image_id" > /dev/null 2>&1; then
            echo -e "  ${GREEN}✓ Successfully deleted${NC}"
        else
            echo -e "  ${YELLOW}⚠ Failed to delete (may be in use)${NC}"
        fi
        echo ""
    fi
  else
    echo -e "${YELLOW}[KEEP]${NC} $image_name (ID: $image_id)"
    [ "$size_condition_met" = false ] && echo "  Reason: Size ${size_mb} MB <= ${SIZE_THRESHOLD_MB} MB"
    [ "$age_condition_met" = false ] && echo "  Reason: Age $days_old < ${AGE_THRESHOLD_DAYS} days"
    echo ""
  fi

  if [ "$size_condition_met" = false ] && [ "$age_condition_met" = false ]; then
    continue
  fi
done < <(
  docker images --format "table {{.ID}}|{{.Repository}}:{{.Tag}}|{{.Size}}" | tail -n +2 | while IFS='|' read -r id repo_tag size_str; do
    image_id=$(docker images -q "$repo_tag" | head -1)
    image_detail=$(docker inspect "$image_id" --format '{{.Size}}' 2>/dev/null || echo "0")
    size=$(echo "$image_detail" | head -1)

    if [ -z "$size" ] || [ "$size" = "0" ]; then
      size_bytes=$(echo "$size_str" | sed 's/[^0-9]//g')
      if [ -z "$size_bytes" ]; then
        size_bytes="0"
      fi
    else
      size_bytes=$size
    fi

    echo "$id|$size_bytes|$repo_tag"
  done
)

echo -e "${GREEN}Docker image cleanup complete!${NC}"
