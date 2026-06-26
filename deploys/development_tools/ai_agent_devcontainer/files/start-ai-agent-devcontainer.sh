#!/bin/bash

set -e

CONFIG_DIR="$HOME/${PROVISION_MACHINES_DIR:-projects/provision-machines}/deploys/development_tools/ai_agent_devcontainer/files"

PORT_MAP_DIR="$HOME/.config/ai-agent-devcontainer"
PORT_MAP_FILE="$PORT_MAP_DIR/port_map"

find_free_port() {
  local port=4096
  while nc -z 127.0.0.1 "$port" 2>/dev/null; do
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

WORKSPACE_DIR=$(pwd)
export WORKSPACE_DIR
WORKSPACE_BASENAME=$(basename "$WORKSPACE_DIR")

WORKING_DIR="/workspaces/${WORKSPACE_BASENAME}"
export WORKING_DIR
export WORKSPACE_BASENAME

if [[ -n "$OPENCODE_PORT" ]]; then
  if ! [[ "$OPENCODE_PORT" =~ ^[0-9]+$ ]] || [[ "$OPENCODE_PORT" -lt 1024 ]] || [[ "$OPENCODE_PORT" -gt 65535 ]]; then
    echo "Error: OPENCODE_PORT must be a valid port number (1024-65535)" >&2
    exit 1
  fi
else
  OPENCODE_PORT=$(lookup_port "$WORKING_DIR")
  if [[ -z "$OPENCODE_PORT" ]]; then
    OPENCODE_PORT=$(find_free_port)
  fi
fi
save_port "$WORKING_DIR" "$OPENCODE_PORT"
export OPENCODE_PORT

# Generate a unique compose project name based on the workspace path
# This allows running multiple devcontainers simultaneously
SANITIZED_PATH=$(echo "$WORKING_DIR" | tr '/' '_' | sed 's/^_//' | sed 's/_$//')
COMPOSE_PROJECT_NAME="ai_devcontainer_${SANITIZED_PATH}"
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

devcontainer up --workspace-folder . --config "$CONFIG_DIR/devcontainer.json" &

ENCODED_PATH=$(echo -n "${WORKING_DIR}" | base64 -w0)
echo "Waiting for http://localhost:${OPENCODE_PORT}/${ENCODED_PATH} to respond..."
until curl -s -f "http://localhost:${OPENCODE_PORT}/${ENCODED_PATH}" > /dev/null; do
  sleep 1
done

echo "http://localhost:${OPENCODE_PORT}/${ENCODED_PATH}"
