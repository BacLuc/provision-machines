#!/bin/bash

set -u

PERSIST_SECONDS=60
COOLDOWN_SECONDS=1800
CHECK_INTERVAL=30

bad_since=0
last_notified=0

while true; do
    now=$(date +%s)
    if acpi -a 2>/dev/null | grep -q "on-line" && acpi -b 2>/dev/null | grep -q "Discharging"; then
        if [ "$bad_since" -eq 0 ]; then
            bad_since=$now
        fi
        if [ $((now - bad_since)) -ge "$PERSIST_SECONDS" ]; then
            if [ "$last_notified" -eq 0 ] || [ $((now - last_notified)) -ge "$COOLDOWN_SECONDS" ]; then
                notify-send "Docking Alert" "Connected to dock but battery is not charging!"
                last_notified=$now
            fi
        fi
    else
        bad_since=0
    fi
    sleep "$CHECK_INTERVAL"
done
