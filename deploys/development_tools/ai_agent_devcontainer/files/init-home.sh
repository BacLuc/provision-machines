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
    "docker compose run --rm e2e npm run lint"
    "docker compose exec frontend npm run lint"
    "docker compose run --rm prettier"
    "docker compose exec api composer run cs-fix"
    "docker compose exec api composer run update-snapshots"
    "docker compose exec api composer run test tests/Api/Users"
    "docker compose --profile e2e run --rm e2e npx playwright test tests/5-cross-browser-tests/login.spec.ts"
    "nvm use"
    "t3 start --host 0.0.0.0 --port 4096"
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
