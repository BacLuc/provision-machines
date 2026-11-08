#!/bin/sh

set -eu

USER="@USER@"
STATE_DIR="@STATE_DIR@"
USER_ID="$(id -u "$USER")"
RUNTIME_DIR="/run/user/$USER_ID"

if [ ! -S "$RUNTIME_DIR/bus" ]; then
    exit 0
fi

runuser -u "$USER" -- env \
    XDG_RUNTIME_DIR="$RUNTIME_DIR" \
    DBUS_SESSION_BUS_ADDRESS="unix:path=$RUNTIME_DIR/bus" \
    notify-send \
    "Provisioning scheduled in two hours" \
    "Run sudo systemctl stop auto-provision.service; sudo sh -c 'printf \"%s\\n\" \"\$(date +%F)\" > $STATE_DIR/stopped-today' to stop today's execution." || true
