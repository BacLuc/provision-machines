import io

from pyinfra import host
from pyinfra.facts.server import Command
from pyinfra.operations import apt, files

if host.data.displaylink_driver["enabled"]:
    installed = "displaylink-driver" in (host.get_fact(Command, "dpkg -l | grep displaylink-driver || true") or "")

    if not installed:
        files.download(
            name="Download Synaptics repository keyring",
            src="https://www.synaptics.com/sites/default/files/Ubuntu/pool/stable/main/all/synaptics-repository-keyring.deb",
            dest="/tmp/synaptics-repository-keyring.deb",
            mode="644",
        )

        apt.deb(
            name="Install Synaptics repository keyring",
            src="/tmp/synaptics-repository-keyring.deb",
            _sudo=True,
        )

        files.put(
            name="Add synaptics list",
            src=io.StringIO("""
deb [signed-by=/usr/share/keyrings/synaptics-repository-keyring.gpg] https://www.synaptics.com/sites/default/files/Ubuntu stable main
deb [signed-by=/usr/share/keyrings/synaptics-repository-keyring.gpg] https://www.synaptics.com/sites/default/files/Ubuntu stable non-free
"""),
            dest="/etc/apt/sources.list.d/synaptics.list",
            user="root",
            group="root",
            mode="644",
            _sudo=True,
        )

        apt.update(
            name="Update APT cache",
            _sudo=True,
        )

        apt.packages(
            name="Install DisplayLink driver",
            packages=["displaylink-driver"],
            _sudo=True,
        )
