import io

from pyinfra import host
from pyinfra.operations import files

if host.data.motd["enable_disk_usage"]:
    files.put(
        name="Show df -h at end",
        src=io.StringIO("""\
#!/bin/sh
set -e

df -h | grep -v snap
"""),
        dest="/etc/update-motd.d/a01-disk-usage",
        _sudo=True,
        mode="755",
    )
