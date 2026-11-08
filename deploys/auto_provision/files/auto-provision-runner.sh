#!/bin/sh

set -eu

USER="@USER@"
HOME_DIR="@HOME@"
CHECKOUT_DIR="@CHECKOUT_DIR@"
BRANCH="@BRANCH@"
STATE_DIR="@STATE_DIR@"
SUCCESS_FILE="$STATE_DIR/last-success-week"
STOP_FILE="$STATE_DIR/stopped-today"
RUNNING_FILE="$STATE_DIR/running"
WEEK="$(date +%G-%V)"
TODAY="$(date +%F)"

mkdir -p "$STATE_DIR"

if [ -f "$SUCCESS_FILE" ] && [ "$(cat "$SUCCESS_FILE")" = "$WEEK" ]; then
    exit 0
fi

if [ -f "$STOP_FILE" ] && [ "$(cat "$STOP_FILE")" = "$TODAY" ]; then
    exit 0
fi

stop_today() {
    printf '%s\n' "$TODAY" > "$STOP_FILE"
    rm -f "$RUNNING_FILE"
    exit 143
}

trap stop_today TERM INT
touch "$RUNNING_FILE"

if [ ! -d "$CHECKOUT_DIR/.git" ]; then
    printf '%s\n' "Checkout not found: $CHECKOUT_DIR" >&2
    exit 1
fi

run_as_user() {
    runuser -u "$USER" -- env HOME="$HOME_DIR" "$@"
}

run_as_user git -C "$CHECKOUT_DIR" fetch --prune origin "$BRANCH"
run_as_user git -C "$CHECKOUT_DIR" checkout --force "$BRANCH"
run_as_user git -C "$CHECKOUT_DIR" reset --hard "origin/$BRANCH"

/usr/local/bin/cleanup-script
runuser -u "$USER" -- env HOME="$HOME_DIR" AUTO_PROVISION_CHECKOUT="$CHECKOUT_DIR" sh -c 'cd "$AUTO_PROVISION_CHECKOUT" && "$HOME/bin/uv" run scripts/run_pyinfra_local.py'
/usr/local/bin/update-script

printf '%s\n' "$WEEK" > "$SUCCESS_FILE"
rm -f "$RUNNING_FILE" "$STOP_FILE"
