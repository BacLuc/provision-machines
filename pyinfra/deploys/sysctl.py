from pyinfra import host
from pyinfra.operations import files, server

sysctl_defaults = {
    "settings": {
        "fs.inotify.max_queued_events": 1048576,
        "fs.inotify.max_user_instances": 1048576,
        "fs.inotify.max_user_watches": 1048576,
    },
}

sysctl = sysctl_defaults.copy()
if host.data.get("sysctl"):
    sysctl.update(host.data.get("sysctl", {}))

if host.data.get("enable_sysctl", False):
    
    files.directory(
        name="Create sysctl.d directory",
        path="/etc/sysctl.d",
        _sudo=True,
        mode="755",
    )
    
    # Build sysctl settings content
    sysctl_content = "# PyInfra managed - Local sysctl settings\n"
    for key, value in sysctl["settings"].items():
        sysctl_content += f"{key} = {value}\n"
    
    files.put(
        name="Create 99-local.conf with sysctl settings",
        dest="/etc/sysctl.d/99-local.conf",
        content=sysctl_content,
        _sudo=True,
        mode="644",
    )
    
    server.shell(
        name="Apply sysctl settings immediately",
        commands=["sysctl --system"],
        _sudo=True,
    )