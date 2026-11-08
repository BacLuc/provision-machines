#!/bin/sh

set -eu

USER="@USER@"
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
    "Run systemctl stop auto-provision.service to stop today's execution." || true
