#!/bin/bash

# IntelliJ VM Settings Applicator
# This script applies VM options to all installed IntelliJ IDEA versions

set -euo pipefail

# Define the target directory and the line to add
TARGET_DIR="${HOME}/.config/JetBrains"
VM_OPTIONS_FILE="idea64.vmoptions"
LINE_TO_ADD="-Xmx8096m"

LOG_FILE="/tmp/intellij-vm-settings.log"

echo "$(date): Starting IntelliJ VM settings application" >> "$LOG_FILE"

# Check if the directory exists
if [ ! -d "$TARGET_DIR" ]; then
  echo "Directory $TARGET_DIR does not exist. No IntelliJ installations found." >> "$LOG_FILE"
  exit 0
fi

# Find all idea64.vmoptions files recursively
find "$TARGET_DIR" -name "$VM_OPTIONS_FILE" -type f | while read -r vm_file; do
  # Check if the line already exists in the file
  if grep -qF -- "$LINE_TO_ADD" "$vm_file"; then
    echo "Skipping: $vm_file (Line already exists)" >> "$LOG_FILE"
  else
    echo "Updating: $vm_file" >> "$LOG_FILE"
    # Append the line to the end of the file
    echo "$LINE_TO_ADD" >> "$vm_file"
  fi
done

echo "$(date): Done applying IntelliJ VM settings" >> "$LOG_FILE"
