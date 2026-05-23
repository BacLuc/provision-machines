from pyinfra import host
from pyinfra.operations import apt, files, server

if host.data.get("okular", {}).get("enabled", False):
    
    apt.packages(
        name="Install okular",
        packages=["okular"],
        _sudo=True,
    )
    
    server.shell(
        name="Create gnome defaults file",
        commands=["touch /etc/gnome/defaults.list"],
        _sudo=True,
    )
    
    files.line(
        name="Set okular as default pdf viewer",
        path="/etc/gnome/defaults.list",
        line="application/pdf=okular.desktop",
        regex="^application/pdf=",
        _sudo=True,
    )