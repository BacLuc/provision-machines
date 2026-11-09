#!/bin/sh

set -eu

CHECKOUT_DIR="{{ checkout_dir }}"
BRANCH="{{ branch }}"
STATE_DIR="{{ state_dir }}"
SUCCESS_FILE="$STATE_DIR/last-success-week"
STOP_FILE="$STATE_DIR/stopped-today"
WEEK=$(date +%G-%V)
TODAY=$(date +%F)

mkdir -p "$STATE_DIR"
exec 9>"$STATE_DIR/lock"
flock -n 9 || exit 0

if [ -f "$SUCCESS_FILE" ] && [ "$(cat "$SUCCESS_FILE")" = "$WEEK" ]; then
    exit 0
fi
if [ -f "$STOP_FILE" ] && [ "$(cat "$STOP_FILE")" = "$TODAY" ]; then
    exit 0
fi

stop_today() {
    printf '%s\n' "$TODAY" > "$STOP_FILE"
    rm -f "$STATE_DIR/running"
    exit 143
}

trap stop_today TERM INT
touch "$STATE_DIR/running"
if [ ! -d "$CHECKOUT_DIR/.git" ]; then
    printf '%s\n' "Checkout not found: $CHECKOUT_DIR" >&2
    exit 1
fi

git -C "$CHECKOUT_DIR" fetch --prune origin "$BRANCH"
git -C "$CHECKOUT_DIR" checkout --force "$BRANCH"
git -C "$CHECKOUT_DIR" reset --hard "origin/$BRANCH"

sudo /usr/local/bin/cleanup-script
cd "$CHECKOUT_DIR"
"$HOME/bin/uv" run scripts/run_pyinfra_local.py
sudo /usr/local/bin/update-script

printf '%s\n' "$WEEK" > "$SUCCESS_FILE"
rm -f "$STATE_DIR/running" "$STOP_FILE"
