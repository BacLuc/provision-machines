from pyinfra import host
from pyinfra.operations import apt, files

if host.data.okular["enabled"]:
    apt.packages(
        name="Install okular",
        packages=["okular"],
        _sudo=True,
    )

    files.file(
        name="Create gnome defaults file",
        path="/etc/gnome/defaults.list",
        touch=True,
        _sudo=True,
        mode="755",
    )

    files.line(
        name="Set okular as default pdf viewer",
        path="/etc/gnome/defaults.list",
        line="^application/pdf=",
        replace="application/pdf=okular.desktop",
        present=True,
        _sudo=True,
    )
