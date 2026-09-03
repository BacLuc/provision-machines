#!/bin/bash

set -u

PERSIST_SECONDS=60
COOLDOWN_SECONDS=1800
CHECK_INTERVAL=30

bad_since=0
last_notified=0

while true; do
    now=$(date +%s)
    ac_adapter=$(acpi -a 2>/dev/null)
    battery=$(acpi -b 2>/dev/null)
    echo "measured acpi -a: '$ac_adapter'"
    echo "measured acpi -b: '$battery'"
    echo "bad_since: $bad_since s, last_notified: $last_notified s"
    if echo "$ac_adapter" | grep -q "off-line" && echo "$battery" | grep -q "Discharging"; then
        if [ "$bad_since" -eq 0 ]; then
            bad_since=$now
        fi
        if [ $((now - bad_since)) -ge "$PERSIST_SECONDS" ]; then
            if [ "$last_notified" -eq 0 ] || [ $((now - last_notified)) -ge "$COOLDOWN_SECONDS" ]; then
                echo "notifying about battery not charging"
                notify-send "Docking Alert" "Connected to dock but battery is not charging!"
                last_notified=$now
            else
              echo "notifying about battery not charging"
            fi
        else
          echo "Battery is not charging, waiting another loop until notifying"
        fi
    else
        echo "charging state is ok"
        bad_since=0
    fi
    sleep "$CHECK_INTERVAL"
done
