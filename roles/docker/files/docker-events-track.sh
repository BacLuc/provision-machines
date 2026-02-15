#!/bin/bash

# Docker Image Usage Tracker - Background Service
# This script runs continuously and tracks docker image usage by monitoring events
# It stores the last used timestamp for each image in a metadata file

METADATA_DIR="${HOME}/.local/share/docker-image-usage"

# Create metadata directory if it doesn't exist
mkdir -p "$METADATA_DIR"

# Function to update image usage
update_image_usage() {
  local image="$1"
  [ -z "$image" ] && return
  
  # Get current timestamp
  local current_time
  current_time=$(date +%s)
  
  # Sanitize image name for use as filename
  local safe_image_name
  safe_image_name=$(echo "$image" | tr '/' '-' | tr ':' '_')
  local metadata_file="${METADATA_DIR}/${safe_image_name}.json"
  
  # Only update if this is newer than what we have
  if [ -f "$metadata_file" ]; then
    local previous_last_used
    previous_last_used=$(jq -r '.last_used // 0' "$metadata_file" 2>/dev/null || echo "0")
    if [ "$current_time" -le "$previous_last_used" ]; then
      return
    fi
  fi
  
  echo "{\"image\": \"$image\", \"last_used\": $current_time}" > "$metadata_file"
}

# Track container start and image pull events continuously
# Using docker events --format with json to get structured data
docker events --format '{{json .}}' 2>/dev/null | while read -r event; do
  [ -z "$event" ] && continue
  
  # Extract event type and image from the JSON
  local event_type
  event_type=$(echo "$event" | jq -r '.Type + "." .Action' 2>/dev/null)
  
  case "$event_type" in
    "container.start")
      local image
      image=$(echo "$event" | jq -r '.Actor.Attributes.image' 2>/dev/null)
      if [ -n "$image" ] && [ "$image" != "null" ]; then
        update_image_usage "$image"
      fi
      ;;
    "image.pull")
      local image_name
      image_name=$(echo "$event" | jq -r '.Actor.Attributes.name' 2>/dev/null)
      if [ -n "$image_name" ] && [ "$image_name" != "null" ]; then
        update_image_usage "$image_name"
      fi
      ;;
  esac
done
