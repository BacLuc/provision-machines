#!/usr/bin/env bash
set -euo pipefail
# Copy dotfiles to $HOME/.dotfiles
TARGET="${HOME}/.dotfiles"
mkdir -p "$TARGET"
# Use rsync to sync source .dotfiles to target
rsync -av --delete .dotfiles/ "$TARGET/"
# Ensure the installed dotfiles are used by devcontainer CLI
# (No further action needed here)
