from pyinfra import host
from pyinfra.operations import apt, files, server

user = host.data.get("user", "ubuntu")

if host.data.get("tmux", {}).get("enabled", False):
    
    apt.packages(
        name="Install tmux tools",
        packages=["tmux"],
        _sudo=True,
    )
    
    files.template(
        name="Add tmux config",
        src="templates/.tmux.conf.j2",
        dest=f"/home/{user}/.tmux.conf",
        mode="644",
    )
    
    server.shell(
        name="Ensure Unix line endings",
        commands=[f"sed -i 's/\\r\\n/\\n/g' /home/{user}/.tmux.conf"],
    )