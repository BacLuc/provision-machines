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

devcontainer up --workspace-folder . --config "$CONFIG_DIR/devcontainer.json"
