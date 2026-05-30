from pyinfra import host
from pyinfra.operations import files

from operations.filesystem import dirname_of

files.directory(
    name="Create update scripts folder",
    path=host.data.update_packages_script["dir"],
    _sudo=True,
    mode="755",
)

files.put(
    name="Copy update script",
    src=f"{dirname_of(__file__)}/files/update-script.sh",
    dest="/usr/local/bin/update-script",
    _sudo=True,
    mode="755",
)

files.put(
    name="Add apt upgrade script",
    src=f"{dirname_of(__file__)}/files/apt-upgrade.sh",
    dest=f"{host.data.update_packages_script['dir']}/apt-upgrade",
    _sudo=True,
    mode="755",
)
