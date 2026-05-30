import io

from pyinfra import host
from pyinfra.operations import files

if host.data.motd["enable_disk_usage"]:
    files.put(
        name="Show df -h at end of motd",
        src=io.StringIO("#!/bin/sh\nset -e\n\ndf -h | grep -v snap\n"),
        dest="/etc/update-motd.d/a01-disk-usage",
        _sudo=True,
        mode="755",
    )
