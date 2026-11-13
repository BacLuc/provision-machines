#!/bin/sh

set -eu

USER_ID=$(id -u)
RUNTIME_DIR="/run/user/$USER_ID"
STATE_DIR="{{ state_dir }}"

if [ ! -S "$RUNTIME_DIR/bus" ]; then
    exit 0
fi

export XDG_RUNTIME_DIR="$RUNTIME_DIR"
export DBUS_SESSION_BUS_ADDRESS="unix:path=$RUNTIME_DIR/bus"

notify-send \
    "Provisioning scheduled in two hours" \
    "Run sudo systemctl stop auto-provision.service; printf '%s\\n' \"\$(date +%F)\" > $STATE_DIR/stopped-today to stop today's execution." || true
