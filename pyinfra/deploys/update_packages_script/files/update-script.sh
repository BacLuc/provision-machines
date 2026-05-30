#!/bin/sh

set -e

log() {
    local message="$*"
    # Send to systemd journal with proper formatting
    printf '%s\n' "$message" | systemd-cat -t update-script -p info
    # Also output to stdout
    printf '%s\n' "$message"
}

log_script_output() {
    local script_name="$1"
    local output="$2"

    if [ -n "$output" ]; then
        log "Output from ${script_name}:"
        # Indent each line for better readability
        printf '%s\n' "$output" | sed 's/^/  /' | while IFS= read -r line; do
            log "$line"
        done
    else
        log "${script_name} completed with no output"
    fi
}

SCRIPT_DIR="$(dirname "$(realpath "$0")")"

if [ "$(id -u)" != "0" ]; then
    log "ERROR: This script must be run with root permissions."
    exit 1
fi

log "Starting update script"

update_scripts_dir="${SCRIPT_DIR}/update-script.d"

if [ ! -d "$update_scripts_dir" ]; then
    log "ERROR: Update scripts directory not found: $update_scripts_dir"
    exit 1
fi

log "Scanning for executable scripts in $update_scripts_dir"

find "$update_scripts_dir" -maxdepth 1 -type f -executable -print | while IFS= read -r script; do
    script_name="$(basename "$script")"
    log "Executing script: $script_name"

    if output=$("$script" 2>&1); then
        exit_code=$?
        log "✓ $script_name completed successfully (exit code: $exit_code)"
        log_script_output "$script_name" "$output"
    else
        exit_code=$?
        log "✗ $script_name failed with exit code: $exit_code"
        log_script_output "$script_name" "$output"

        exit $exit_code
    fi
done

log "Update script completed"
