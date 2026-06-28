#!/bin/bash
# Open an interactive zsh shell in the ai_agent_devcontainer for the current
# directory. The container must already be running (use start-ai-agent-devcontainer).

set -e

WORKSPACE_BASENAME=$(basename "$(pwd)")
WORKING_DIR="/workspaces/${WORKSPACE_BASENAME}"
SANITIZED_PATH=$(echo "$WORKING_DIR" | tr '/' '_' | sed 's/^_//' | sed 's/_$//')
COMPOSE_PROJECT_NAME="ai_devcontainer_${SANITIZED_PATH}"

CONTAINER=$(docker ps \
  --filter "label=com.docker.compose.project=${COMPOSE_PROJECT_NAME}" \
  --filter "label=com.docker.compose.service=devcontainer" \
  --format "{{.ID}}" | head -1)

if [[ -z "$CONTAINER" ]]; then
  echo "No running ai_agent_devcontainer found for '$(pwd)'." >&2
  echo "Start one first with: start-ai-agent-devcontainer" >&2
  exit 1
fi

exec docker exec -it -w "/workspaces/${WORKSPACE_BASENAME}" "$CONTAINER" zsh
