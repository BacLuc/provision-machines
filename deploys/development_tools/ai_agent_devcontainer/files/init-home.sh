#!/bin/bash
#
# Best-effort, idempotent seeding of shell history for the AI agent devcontainer.
# Runs on every container start via postStartCommand. A sentinel file makes the
# actual seeding happen only once per (shared) home volume. This script must
# never fail the container start, hence the trailing `exit 0`.
#
# nvm availability in interactive zsh is handled separately and globally via
# /etc/zsh/zshrc in the Dockerfile, so it is intentionally not touched here.

HOME_DIR="${HOME:-/home/codespace}"
BASH_HISTORY_FILE="$HOME_DIR/.bash_history"
ZSH_HISTORY_FILE="$HOME_DIR/.zsh_history"
SEED_DONE_FILE="$HOME_DIR/.ai-devcontainer-history-seeded"

SEED_COMMANDS=(
    "uv sync --all-extras"
    "uv run scripts/run_pyinfra_local.py"
    "uv run scripts/lint.py"
    "docker compose up -d"
    "nvm use"
)

if [ ! -f "$SEED_DONE_FILE" ]; then
    timestamp=$(date +%s)
    for cmd in "${SEED_COMMANDS[@]}"; do
        # bash history: one command per line
        printf '%s\n' "$cmd" >> "$BASH_HISTORY_FILE"
        # zsh extended history format: ': <timestamp>:<elapsed>;<command>'
        printf ': %s:0;%s\n' "$timestamp" "$cmd" >> "$ZSH_HISTORY_FILE"
    done
    touch "$SEED_DONE_FILE"
fi

exit 0
