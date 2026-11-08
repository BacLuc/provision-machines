#!/bin/bash

set -e

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

DEVCONTAINER_WAIT_TIMEOUT="${DEVCONTAINER_WAIT_TIMEOUT:-120}"
if ! [[ "$DEVCONTAINER_WAIT_TIMEOUT" =~ ^[0-9]+$ ]]; then
  echo "Error: DEVCONTAINER_WAIT_TIMEOUT must be a nonnegative integer" >&2
  exit 1
fi

if [[ -z "${OPENCODE_SERVER_PASSWORD:-}" ]]; then
  mkdir -p "$PORT_MAP_DIR"
  [[ -s "$PORT_MAP_DIR/password" ]] || openssl rand -hex 16 > "$PORT_MAP_DIR/password"
  chmod 600 "$PORT_MAP_DIR/password"
  OPENCODE_SERVER_PASSWORD=$(<"$PORT_MAP_DIR/password")
fi
export OPENCODE_SERVER_PASSWORD

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

startup_log=$(mktemp)
devcontainer_wait_timeout=${DEVCONTAINER_WAIT_TIMEOUT:-30}
cleanup() {
  local status=$?
  if [[ $status -ne 0 && -n "${devcontainer_pid:-}" ]]; then
    if kill -0 "$devcontainer_pid" 2>/dev/null; then
      kill "$devcontainer_pid" 2>/dev/null || true
    fi
    wait "$devcontainer_pid" 2>/dev/null || true
    devcontainer down --workspace-folder . --config "$CONFIG_DIR/devcontainer.json" >/dev/null 2>&1 || true
  elif [[ -n "${devcontainer_pid:-}" ]]; then
    wait "$devcontainer_pid" 2>/dev/null || true
  fi
  rm -f "$startup_log"
  exit "$status"
}
trap cleanup EXIT

devcontainer up --workspace-folder . --config "$CONFIG_DIR/devcontainer.json" >"$startup_log" 2>&1 &
devcontainer_pid=$!
devcontainer_status=

base_url="http://localhost:${OPENCODE_PORT}"
echo "Waiting for ${base_url} to respond..."
ready=false
for ((wait_seconds = 0; wait_seconds < DEVCONTAINER_WAIT_TIMEOUT; wait_seconds++)); do
  if [[ -z "$devcontainer_status" ]] && ! kill -0 "$devcontainer_pid" 2>/dev/null; then
    if wait "$devcontainer_pid"; then
      devcontainer_status=0
    else
      devcontainer_status=$?
    fi
    if [[ "$devcontainer_status" -ne 0 ]]; then
      cat "$startup_log" >&2
      echo "Error: devcontainer failed to start" >&2
      exit 1
    fi
  fi
  if response=$(curl --connect-timeout 2 --max-time 5 -fsS -u "opencode:${OPENCODE_SERVER_PASSWORD}" "${base_url}/api/config" 2>/dev/null) && printf %s "$response" | python3 -c 'import json, sys; json.load(sys.stdin)' 2>/dev/null; then
    ready=true
    break
  fi
  sleep 1
done

if [[ "$ready" != true ]]; then
  cat "$startup_log" >&2
  echo "Error: timed out waiting for ${base_url} to respond" >&2
  exit 1
fi

for ((seconds_waited = 0; seconds_waited < devcontainer_wait_timeout; seconds_waited++)); do
  if ! kill -0 "$devcontainer_pid" 2>/dev/null; then
    if wait "$devcontainer_pid"; then
      devcontainer_status=0
    else
      devcontainer_status=$?
    fi
    if [[ "$devcontainer_status" -ne 0 ]]; then
      cat "$startup_log" >&2
      echo "Error: devcontainer failed to start" >&2
      exit 1
    fi
    break
  fi
  sleep 1
done
if [[ -z "$devcontainer_status" ]]; then
  cat "$startup_log" >&2
  echo "Error: timed out waiting for devcontainer to finish starting" >&2
  exit 1
fi

if ! response=$(curl --connect-timeout 2 --max-time 5 -fsS -X POST -u "opencode:${OPENCODE_SERVER_PASSWORD}" "${base_url}/api/pair"); then
  echo "Error: could not request pairing code" >&2
  echo "Fallback: use the password from ~/.config/ai-agent-devcontainer/password to log in at ${base_url}" >&2
  exit 1
fi
code=$(printf %s "$response" | python3 -c 'import json, sys; value = json.load(sys.stdin).get("code", ""); print(value if isinstance(value, str) else "")' 2>/dev/null || true)
if [[ -z "$code" ]] || [[ ! "$code" =~ ^[A-Za-z0-9_-]+$ ]]; then
  echo "Error: could not extract pairing code from: $response" >&2
  echo "Fallback: use the password from ~/.config/ai-agent-devcontainer/password to log in at ${base_url}" >&2
  exit 1
fi
opencode_url="${base_url}/auth/connect/${code}"

printf %s "$opencode_url" | (xclip -selection clipboard 2>/dev/null || wl-copy 2>/dev/null || pbcopy 2>/dev/null || true)

if [[ "${ai_agent_devcontainer_open_url:-true}" = "true" ]]; then
  open "$opencode_url" || true
fi

echo "$opencode_url"
