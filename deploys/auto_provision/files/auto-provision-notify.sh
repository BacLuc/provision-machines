#!/bin/sh

set -eu

USER_ID=$(id -u)
RUNTIME_DIR="/run/user/$USER_ID"
STATE_DIR="{{ state_dir }}"

if [ ! -S "$RUNTIME_DIR/bus" ]; then
    exit 0
fi

notify-send \
    "Provisioning scheduled in two hours" \
    "Run sudo systemctl stop auto-provision.service; printf '%s\\n' \"\$(date +%F)\" > $STATE_DIR/stopped-today to stop today's execution." || true
