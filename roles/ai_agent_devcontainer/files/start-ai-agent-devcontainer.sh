#!/bin/bash

set -e

CONFIG_DIR="$HOME/${PROVISION_MACHINES_DIR:-projects/provision-machines}/roles/ai_agent_devcontainer/files"

WORKSPACE_DIR=$(pwd)
WORKSPACE_BASENAME=$(basename "$WORKSPACE_DIR")

WORKING_DIR="/workspaces/${WORKSPACE_BASENAME}"
export WORKING_DIR
export WORKSPACE_BASENAME

# Generate a unique compose project name based on the workspace path
# This allows running multiple devcontainers simultaneously
SANITIZED_PATH=$(echo "$WORKING_DIR" | tr '/' '_' | sed 's/^_//' | sed 's/_$//')
COMPOSE_PROJECT_NAME="ai_devcontainer_${SANITIZED_PATH}"
export COMPOSE_PROJECT_NAME

devcontainer up --workspace-folder . --config "$CONFIG_DIR/devcontainer.json"
