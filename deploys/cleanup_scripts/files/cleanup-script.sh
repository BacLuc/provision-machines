#/bin/sh

set -e

log() {
  systemd-cat -t update-script -p info echo "$*"
  echo "$*"
}

SCRIPT_DIR="$(dirname $(realpath "$0"))"

if [ "$(id -u)" != "0" ]; then
  echo "This script must be run with root permissions."
  exit 1
fi

log "Starting update script"
cleanup_scripts_dir=${SCRIPT_DIR}/cleanup_scripts.d
for script in $(ls ${cleanup_scripts_dir}); do
  log "Running ${cleanup_scripts_dir}/${script}"
  if [ -x "${cleanup_scripts_dir}/${script}" ]; then
    log $(${cleanup_scripts_dir}/${script} 2>&1)
  fi
done
