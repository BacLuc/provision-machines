#!/bin/bash

# Docker Cleanup Script
# This script removes Docker images that are larger than 200MB and haven't been used in over 2 months
# Images that meet both criteria are considered safe to delete

set -euo pipefail

# Thresholds
SIZE_THRESHOLD_MB="200"
SIZE_THRESHOLD=$((SIZE_THRESHOLD_MB * 1024 * 1024))  # Convert to bytes
AGE_THRESHOLD_DAYS=60  # Approx. 2 months

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'  # No Color

echo -e "${GREEN}Starting Docker Image Cleanup...${NC}"
echo "Images must meet both conditions to be deleted:"
echo "  - Size > ${SIZE_THRESHOLD_MB} MB"
echo "  - Not used in the last 2 months (${AGE_THRESHOLD_DAYS} days)"
echo ""

# Get current timestamp in seconds
CURRENT_TIME=$(date +%s)

# Iterate through all images
while IFS= read -r image_info; do
  # Skip empty lines
  [ -z "$image_info" ] && continue

  # Extract image ID, size, and last used timestamp
  # Format: IMAGE_ID|SIZE|LAST_USED_TIMESTAMP|REPOSITORY:TAG
  image_id=$(echo "$image_info" | cut -d'|' -f1)
  size_bytes=$(echo "$image_info" | cut -d'|' -f2)
  last_used=$(echo "$image_info" | cut -d'|' -f3)
  image_name=$(echo "$image_info" | cut -d'|' -f4)

  # Convert size to human-readable format for display
  size_mb=$((size_bytes / 1024 / 1024))

  # Check size condition (must be greater than threshold)
  if [ "$size_bytes" -gt "$SIZE_THRESHOLD" ]; then
    size_condition_met=true
  else
    size_condition_met=false
  fi

  # Check age condition (must be older than threshold)
  if [ -z "$last_used" ] || [ "$last_used" = "0" ]; then
    # Image has never been used, treat it as old
    age_condition_met=true
    days_old="Never used"
  else
    # Calculate age in days
    age_seconds=$((CURRENT_TIME - last_used))
    age_days=$((age_seconds / 86400))

    if [ "$age_days" -ge "$AGE_THRESHOLD_DAYS" ]; then
      age_condition_met=true
    else
      age_condition_met=false
    fi

    days_old="${age_days} days old"
  fi

  # Display information
  if [ "$size_condition_met" = true ] && [ "$age_condition_met" = true ]; then
    echo -e "${RED}[DELETE]${NC} $image_name (ID: $image_id)"
    echo "  Size: ${size_mb} MB ($size_bytes bytes)"
    echo "  Age: $days_old"

    DRY_RUN=${DRY_RUN:-true}

    if [[ "$DRY_RUN" != "true" ]]; then
        # Delete the image
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

  # Display skipped images for debugging
  if [ "$size_condition_met" = false ] && [ "$age_condition_met" = false ]; then
    continue
  fi
done < <(
  docker images --format "table {{.ID}}|{{.Repository}}:{{.Tag}}|{{.Size}}" | tail -n +2 | while IFS='|' read -r id repo_tag size_str; do
    # Get image inspect details
    image_detail=$(docker inspect "$id" --format '{{.Size}}|{{.Metadata.LastTagTime}}' 2>/dev/null || echo "0|0")
    size=$(echo "$image_detail" | cut -d'|' -f1)
    last_tagged=$(echo "$image_detail" | cut -d'|' -f2)

    # Check if container was run from this image recently
    last_used=0
    while IFS= read -r cid; do
      [ -z "$cid" ] && continue
      # Get container state and timestamps
      state=$(docker inspect "$cid" --format '{{.State.Status}}' 2>/dev/null || echo "")
      if [ "$state" = "running" ]; then
        finished=$(docker inspect "$cid" --format '{{.State.StartedAt}}' 2>/dev/null || echo "0")
      else
        finished=$(docker inspect "$cid" --format '{{.State.FinishedAt}}' 2>/dev/null || echo "0")
      fi
      # Convert to timestamp
      if [ -n "$finished" ] && [ "$finished" != "0001-01-01T00:00:00Z" ]; then
        finished_ts=$(date -u -d "$finished" +%s 2>/dev/null || echo "0")
        if [ "$finished_ts" -gt "$last_used" ]; then
          last_used=$finished_ts
        fi
      fi
    done < <(docker ps -a --filter "ancestor=$id" --format "{{.ID}}" 2>/dev/null)

    # If no container was found, use the image creation time
    if [ "$last_used" = "0" ]; then
      if [ "$last_tagged" != "0001-01-01T00:00:00Z" ] && [ -n "$last_tagged" ]; then
        last_used=$(date -u -d "$last_tagged" +%s 2>/dev/null || echo "0")
      else
        created=$(docker inspect "$id" --format '{{.Created}}' 2>/dev/null || echo "0")
        if [ "$created" != "0001-01-01T00:00:00Z" ] && [ -n "$created" ]; then
          last_used=$(date -u -d "$created" +%s 2>/dev/null || echo "0")
        else
          last_used="0"
        fi
      fi
    fi

    echo "$id|$size|$last_used|$repo_tag"
  done
)

echo -e "${GREEN}Docker image cleanup complete!${NC}"
