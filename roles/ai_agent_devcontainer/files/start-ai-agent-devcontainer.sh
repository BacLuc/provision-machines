#!/bin/bash

set -e

CONFIG_DIR="$HOME/${PROVISION_MACHINES_DIR:-projects/provision-machines}/roles/ai_agent_devcontainer/files"

WORKSPACE_DIR=$(pwd)
WORKSPACE_BASENAME=$(basename "$WORKSPACE_DIR")

WORKING_DIR="/workspaces/${WORKSPACE_BASENAME}"

devcontainer up --workspace-folder . --config "$CONFIG_DIR/devcontainer.json"
