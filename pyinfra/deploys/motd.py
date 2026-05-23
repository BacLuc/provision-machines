from pyinfra import host
from pyinfra.operations import files

motd = host.data.get("motd", {})

if motd.get("enable_disk_usage", False):
    
    files.put(
        name="Show df -h at end",
        dest="/etc/update-motd.d/a01-disk-usage",
        content="""#!/bin/sh
set -e

df -h | grep -v snap
""",
        _sudo=True,
        mode="755",
    )