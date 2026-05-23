from pyinfra import host
from pyinfra.operations import (
    files,
)

# Set facts for cleanup_scripts
cleanup_scripts_dir = "/usr/local/bin/cleanup_scripts.d"

# Create cleanup scripts folder
files.directory(
    name="Create cleanup scripts folder",
    path=cleanup_scripts_dir,
    _sudo=True,
    mode="755",
)

# Copy cleanup script
files.put(
    name="Copy cleanup script",
    src="files/cleanup-script.sh",
    dest="/usr/local/bin/cleanup-script",
    _sudo=True,
    mode="755",
)