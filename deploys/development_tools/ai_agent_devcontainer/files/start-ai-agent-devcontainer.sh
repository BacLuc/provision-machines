#!/bin/bash

set -e

DEVCONTAINER_PID=""
WORKSPACE_DIR=""
COMPOSE_PROJECT_NAME=""
CONFIG_DIR=""
PORT_MAP_KEY=""
TEMP_WORKSPACE=false
cleaned_up=false

cleanup() {
  if [[ "$cleaned_up" == true ]]; then
    return
  fi
  cleaned_up=true
  if [[ -n "$DEVCONTAINER_PID" ]] && kill -0 "$DEVCONTAINER_PID" 2>/dev/null; then
    kill "$DEVCONTAINER_PID" 2>/dev/null || true
    wait "$DEVCONTAINER_PID" 2>/dev/null || true
  fi
  if [[ -n "$WORKSPACE_DIR" ]]; then
    docker compose -p "$COMPOSE_PROJECT_NAME" -f "$CONFIG_DIR/compose.yml" down 2>/dev/null || true
    if [[ "$TEMP_WORKSPACE" == true && -f "$PORT_MAP_FILE" ]]; then
      awk -v d="$PORT_MAP_KEY" '$1 != d' "$PORT_MAP_FILE" > "$PORT_MAP_FILE.tmp"
      mv "$PORT_MAP_FILE.tmp" "$PORT_MAP_FILE"
    fi
  fi
}

handle_signal() {
  cleanup
  exit "$1"
}

trap 'handle_signal 130' INT
trap 'handle_signal 143' TERM

NO_OPEN=false
DOWN=false
while [[ $# -gt 0 ]]; do
  case "$1" in
    --workspace-dir)
      WORKSPACE_DIR="$2"
      shift 2
      ;;
    --no-open)
      NO_OPEN=true
      shift
      ;;
    --down)
      DOWN=true
      shift
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 2
      ;;
  esac
done

CONFIG_DIR="$HOME/${PROVISION_MACHINES_DIR:-projects/provision-machines}/deploys/development_tools/ai_agent_devcontainer/files"

PORT_MAP_DIR="$HOME/.config/ai-agent-devcontainer"
PORT_MAP_FILE="$PORT_MAP_DIR/port_map"

export BUILDX_BAKE_ENTITLEMENTS_FS=0

find_free_port() {
  local port=4096
  local mapped_ports
  mapped_ports=$(awk '{print $2}' "$PORT_MAP_FILE" 2>/dev/null || true)
  while nc -z 127.0.0.1 "$port" 2>/dev/null || grep -qx "$port" <<< "$mapped_ports"; do
    port=$((port + 1))
    if [[ $port -gt 9999 ]]; then
      port=$((RANDOM % 60000 + 4000))
    fi
  done
  echo "$port"
}

lookup_port() {
  local dir="$1"
  if [[ -f "$PORT_MAP_FILE" ]]; then
    awk -v d="$dir" '$1 == d { print $2 }' "$PORT_MAP_FILE"
  fi
}

save_port() {
  local dir="$1"
  local port="$2"
  mkdir -p "$PORT_MAP_DIR"
  touch "$PORT_MAP_FILE"
  local existing
  existing=$(awk -v d="$dir" '$1 != d' "$PORT_MAP_FILE" 2>/dev/null || true)
  {
    printf "%s\n" "$existing"
    printf "%s %s\n" "$dir" "$port"
  } | grep -v '^$' | sort > "$PORT_MAP_FILE"
}

WORKSPACE_DIR=${WORKSPACE_DIR:-$(pwd)}
WORKSPACE_DIR=$(realpath "$WORKSPACE_DIR")
export WORKSPACE_DIR
WORKSPACE_BASENAME=$(basename "$WORKSPACE_DIR")
if [[ "$WORKSPACE_BASENAME" == "workspace" ]]; then
  TEMP_WORKSPACE=true
  PORT_MAP_KEY="$WORKSPACE_DIR"
else
  PORT_MAP_KEY="/workspaces/$WORKSPACE_BASENAME"
fi

WORKING_DIR="/workspaces/${WORKSPACE_BASENAME}"
export WORKING_DIR
export WORKSPACE_BASENAME

if [[ -n "$OPENCODE_PORT" ]]; then
  if ! [[ "$OPENCODE_PORT" =~ ^[0-9]+$ ]] || [[ "$OPENCODE_PORT" -lt 1024 ]] || [[ "$OPENCODE_PORT" -gt 65535 ]]; then
    echo "Error: OPENCODE_PORT must be a valid port number (1024-65535)" >&2
    exit 1
  fi
else
  OPENCODE_PORT=$(lookup_port "$PORT_MAP_KEY")
  if [[ -z "$OPENCODE_PORT" ]]; then
    OPENCODE_PORT=$(find_free_port)
  fi
fi
save_port "$PORT_MAP_KEY" "$OPENCODE_PORT"
export OPENCODE_PORT

# Generate a unique compose project name based on the workspace path
# This allows running multiple devcontainers simultaneously
SANITIZED_PATH=$(echo "$WORKING_DIR" | tr '/' '_' | sed 's/^_//' | sed 's/_$//')
COMPOSE_PROJECT_NAME="ai_devcontainer_${SANITIZED_PATH}"
if [[ "$WORKSPACE_BASENAME" == "workspace" ]]; then
  WORKSPACE_PROJECT_SUFFIX=$(printf '%s' "$WORKSPACE_DIR" | sha256sum | cut -c1-8)
  COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME}_${WORKSPACE_PROJECT_SUFFIX}"
fi
export COMPOSE_PROJECT_NAME

export GIT_AUTHOR_NAME=$(git config user.name)
export GIT_AUTHOR_EMAIL=$(git config user.email)

mkdir -p /tmp/noworktree
if [[ -f $WORKSPACE_DIR/.git ]]; then
  if grep -q "../" $WORKSPACE_DIR/.git ; then
    WORKTREE_DIR=$(git rev-parse --git-dir)
    WORKTREE_GIT_DIR=$(basename $(realpath $WORKTREE_DIR/../../../))
    RELATIVE_WORKTREE_SOURCE=$(realpath --relative-to=. $WORKTREE_DIR)
    if echo "$RELATIVE_WORKTREE_SOURCE" | grep -q "../"; then
      export GIT_WORKTREE_SOURCE=$(realpath $WORKTREE_DIR/../../../)
      export GIT_WORKTREE_TARGET="/workspaces/$WORKTREE_GIT_DIR"
    fi
    if echo "$RELATIVE_WORKTREE_SOURCE" | grep -q "../../"; then
      export GIT_WORKTREE_TARGET="/$WORKTREE_GIT_DIR"
    fi
  fi
fi

if [[ "$DOWN" == true ]]; then
  docker compose -p "$COMPOSE_PROJECT_NAME" -f "$CONFIG_DIR/compose.yml" down
  if [[ "$TEMP_WORKSPACE" == true && -f "$PORT_MAP_FILE" ]]; then
    awk -v d="$PORT_MAP_KEY" '$1 != d' "$PORT_MAP_FILE" > "$PORT_MAP_FILE.tmp"
    mv "$PORT_MAP_FILE.tmp" "$PORT_MAP_FILE"
  fi
  cleaned_up=true
  exit 0
fi

devcontainer up --workspace-folder "$WORKSPACE_DIR" --config "$CONFIG_DIR/devcontainer.json" &
DEVCONTAINER_PID=$!

encoded_path=$(echo -n "${WORKING_DIR}" | base64 -w0)
opencode_url="http://localhost:${OPENCODE_PORT}/${encoded_path}"
echo "Waiting for ${opencode_url} to respond..."
if [[ "$NO_OPEN" == false && "${ai_agent_devcontainer_open_url:-true}" = "true" ]]; then
  open "$opencode_url"
fi
deadline=$((SECONDS + ${DEVCONTAINER_START_TIMEOUT:-120}))
until [[ -n "$(docker compose -p "$COMPOSE_PROJECT_NAME" -f "$CONFIG_DIR/compose.yml" ps --status running --services devcontainer 2>/dev/null)" ]] && curl -s -f "${opencode_url}" > /dev/null; do
  if (( SECONDS >= deadline )); then
    echo "Timed out waiting for devcontainer service in Compose project ${COMPOSE_PROJECT_NAME} at ${opencode_url}" >&2
    docker compose -p "$COMPOSE_PROJECT_NAME" -f "$CONFIG_DIR/compose.yml" ps -a >&2 || true
    docker compose -p "$COMPOSE_PROJECT_NAME" -f "$CONFIG_DIR/compose.yml" logs --no-color --tail=100 devcontainer >&2 || true
    cleanup
    exit 1
  fi
  if ! kill -0 "$DEVCONTAINER_PID" 2>/dev/null; then
    echo "devcontainer up exited before ${COMPOSE_PROJECT_NAME}/devcontainer became ready" >&2
    docker compose -p "$COMPOSE_PROJECT_NAME" -f "$CONFIG_DIR/compose.yml" ps -a >&2 || true
    docker compose -p "$COMPOSE_PROJECT_NAME" -f "$CONFIG_DIR/compose.yml" logs --no-color --tail=100 devcontainer >&2 || true
    cleanup
    exit 1
  fi
  sleep 1
done

echo "${opencode_url}"
