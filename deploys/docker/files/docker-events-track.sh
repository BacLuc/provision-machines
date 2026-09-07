#!/bin/bash

METADATA_DIR="${HOME}/.local/share/docker-image-usage"
VOLUME_USAGE_DIR="${HOME}/.local/share/docker-volume-usage"
NETWORK_USAGE_DIR="${HOME}/.local/share/docker-network-usage"

mkdir -p "$METADATA_DIR" "$VOLUME_USAGE_DIR" "$NETWORK_USAGE_DIR"

write_usage_metadata() {
  local kind="$1"
  local name="$2"
  local dir="$3"
  [ -z "$name" ] && return

  local current_time
  current_time=$(date +%s)

  local safe_name
  safe_name=$(echo "$name" | tr '/' '-' | tr ':' '_')
  local metadata_file="${dir}/${safe_name}.json"

  if [ -f "$metadata_file" ]; then
    local previous_last_used
    previous_last_used=$(jq -r '.last_used // 0' "$metadata_file" 2>/dev/null || echo "0")
    if [ "$current_time" -le "$previous_last_used" ]; then
      return
    fi
  fi

  echo "{\"${kind}\": \"$name\", \"name\": \"$name\", \"last_used\": $current_time}" > "$metadata_file"
}

delete_usage_metadata() {
  local name="$1"
  local dir="$2"
  [ -z "$name" ] && return

  local safe_name
  safe_name=$(echo "$name" | tr '/' '-' | tr ':' '_')
  local metadata_file="${dir}/${safe_name}.json"

  rm -f "$metadata_file"
}

docker events --format '{{json .}}' 2>/dev/null | while read -r event; do
  [ -z "$event" ] && continue

  event_type=$(echo "$event" | jq -r '.Type + "." + .Action' 2>/dev/null)

  case "$event_type" in
    "container.start")
      cid=$(echo "$event" | jq -r '.Actor.ID' 2>/dev/null)
      image=$(echo "$event" | jq -r '.Actor.Attributes.image' 2>/dev/null)
      if [ -n "$image" ] && [ "$image" != "null" ]; then
        write_usage_metadata "image" "$image" "$METADATA_DIR"
      fi
      if [ -n "$cid" ] && [ "$cid" != "null" ]; then
        for vol in $(docker inspect "$cid" --format '{{range .Mounts}}{{if eq .Type "volume"}}{{.Name}} {{end}}{{end}}' 2>/dev/null); do
          write_usage_metadata "volume" "$vol" "$VOLUME_USAGE_DIR"
        done
        for net in $(docker inspect "$cid" --format '{{range $k, $v := .NetworkSettings.Networks}}{{$k}} {{end}}' 2>/dev/null); do
          write_usage_metadata "network" "$net" "$NETWORK_USAGE_DIR"
        done
      fi
      ;;
    "image.pull")
      image_name=$(echo "$event" | jq -r '.Actor.Attributes.name' 2>/dev/null)
      if [ -n "$image_name" ] && [ "$image_name" != "null" ]; then
        write_usage_metadata "image" "$image_name" "$METADATA_DIR"
      fi
      ;;
    "volume.create"|"volume.mount"|"volume.unmount")
      vol_name=$(echo "$event" | jq -r '.Actor.ID' 2>/dev/null)
      if [ -n "$vol_name" ] && [ "$vol_name" != "null" ]; then
        write_usage_metadata "volume" "$vol_name" "$VOLUME_USAGE_DIR"
      fi
      ;;
    "volume.destroy")
      vol_name=$(echo "$event" | jq -r '.Actor.ID' 2>/dev/null)
      if [ -n "$vol_name" ] && [ "$vol_name" != "null" ]; then
        delete_usage_metadata "$vol_name" "$VOLUME_USAGE_DIR"
      fi
      ;;
    "network.create"|"network.connect"|"network.disconnect")
      net_name=$(echo "$event" | jq -r '.Actor.Attributes.name' 2>/dev/null)
      if [ -n "$net_name" ] && [ "$net_name" != "null" ]; then
        write_usage_metadata "network" "$net_name" "$NETWORK_USAGE_DIR"
      fi
      ;;
    "network.destroy")
      net_name=$(echo "$event" | jq -r '.Actor.Attributes.name' 2>/dev/null)
      if [ -n "$net_name" ] && [ "$net_name" != "null" ]; then
        delete_usage_metadata "$net_name" "$NETWORK_USAGE_DIR"
      fi
      ;;
  esac
done
