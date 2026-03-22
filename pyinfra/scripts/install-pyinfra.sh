#!/bin/bash
# Script to install pyinfra locally

set -e

echo "Installing pyinfra..."

# Check if pipx is available (preferred) or use pip with --break-system-packages
if command -v pipx &> /dev/null; then
    echo "Using pipx to install pyinfra..."
    pipx install pyinfra
elif command -v pip3 &> /dev/null; then
    echo "Using pip to install pyinfra..."
    pip3 install pyinfra --break-system-packages
else
    echo "Error: pip or pipx not found. Please install Python pipx or pip."
    exit 1
fi

echo "pyinfra installed successfully!"
pyinfra --version
