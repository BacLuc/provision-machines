#!/bin/bash

set -e

# Define the central configuration directory on the host
CONFIG_DIR="$HOME/.config/ai_agent_devcontainer"

# Ensure the central configuration directory exists
mkdir -p "$CONFIG_DIR"

# Check if devcontainer.json and Dockerfile exist in the central config directory
if [ ! -f "$CONFIG_DIR/devcontainer.json" ]; then
    echo "Error: $CONFIG_DIR/devcontainer.json not found."
    echo "Please ensure the ai_agent_devcontainer ansible role has been run correctly."
    exit 1
fi

if [ ! -f "$CONFIG_DIR/Dockerfile" ]; then
    echo "Error: $CONFIG_DIR/Dockerfile not found."
    echo "Please ensure the ai_agent_devcontainer ansible role has been run correctly."
    exit 1
fi

# Check if opencode config files exist
if [ ! -f "$HOME/.config/opencode/provider-config.json" ]; then
    echo "Warning: $HOME/.config/opencode/provider-config.json not found."
    echo "Opencode might not function correctly without provider configuration."
fi

if [ ! -f "$HOME/.config/opencode/api-keys.json" ]; then
    echo "Warning: $HOME/.config/opencode/api-keys.json not found."
    echo "Opencode might not function correctly without API keys."
fi

if [ ! -d "$HOME/.config/opencode/agents" ]; then
    echo "Warning: $HOME/.config/opencode/agents directory not found."
    echo "Opencode might not find agent descriptions."
fi

# Get the current working directory (workspace)
WORKSPACE_DIR=$(pwd)
WORKSPACE_BASENAME=$(basename "$WORKSPACE_DIR")

# Define a unique name for the devcontainer image and container to avoid conflicts
IMAGE_NAME="ai-agent-devcontainer-image-$WORKSPACE_BASENAME"
CONTAINER_NAME="ai-agent-devcontainer-$WORKSPACE_BASENAME"

echo "Starting AI Agent DevContainer for workspace: $WORKSPACE_DIR"
echo "Container name will be: $CONTAINER_NAME"
echo "Image name will be: $IMAGE_NAME"

# Navigate to the central config directory to run devcontainer build
# The devcontainer CLI uses the devcontainer.json in the current directory.
cd "$CONFIG_DIR"

# Build the devcontainer image
echo "Building devcontainer image: $IMAGE_NAME..."
devcontainer build --workspace-folder "$WORKSPACE_DIR" --config "$CONFIG_DIR/devcontainer.json" --image-name "$IMAGE_NAME"

# Check if a container with the same name already exists and remove it
if [ "$(docker ps -aq -f name=$CONTAINER_NAME)" ]; then
    echo "Removing existing container: $CONTAINER_NAME"
    docker rm -f "$CONTAINER_NAME"
fi

# Run the devcontainer
echo "Running devcontainer: $CONTAINER_NAME..."
# We use --workspace-folder to mount the current dir.
# The mounts for opencode configs are handled by devcontainer.json.
# We pass 'opencode --webui' as the command to run inside the container.
devcontainer run --workspace-folder "$WORKSPACE_DIR" --config "$CONFIG_DIR/devcontainer.json" --image-name "$IMAGE_NAME" --override-name "$CONTAINER_NAME" opencode --webui

echo "AI Agent DevContainer has stopped."
echo "To manually remove the container, run: docker rm $CONTAINER_NAME"
echo "To manually remove the image, run: docker rmi $IMAGE_NAME"

# Navigate back to the original workspace directory
cd "$WORKSPACE_DIR"