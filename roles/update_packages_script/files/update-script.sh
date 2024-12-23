#/bin/sh

set -e

log() {
  systemd-cat -t update-script -p info echo "'$*'"
}

SCRIPT_DIR="$(dirname $(realpath "$0"))"

if [ "$(id -u)" != "0" ]; then
  echo "This script must be run with root permissions."
  exit 1
fi

log "Starting update script"
update_scripts_dir=${SCRIPT_DIR}/update-script.d
for script in $(ls ${update_scripts_dir}); do
  log "Running ${update_scripts_dir}/${script}"
  if [ -x "${update_scripts_dir}/${script}" ]; then
    systemd-cat -t update-script -p info ${update_scripts_dir}/${script}
  fi
done
