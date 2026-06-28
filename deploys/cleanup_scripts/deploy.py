from pyinfra import host
from pyinfra.operations import files

from operations.filesystem import dirname_of

files.directory(
    name="Create cleanup scripts folder",
    path=host.data.cleanup_scripts["dir"],
    _sudo=True,
    mode="755",
)

files.put(
    name="Copy cleanup script",
    src=f"{dirname_of(__file__)}/files/cleanup-script.sh",
    dest="/usr/local/bin/cleanup-script",
    _sudo=True,
    mode="755",
)
