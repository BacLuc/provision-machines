from pyinfra import host
from pyinfra.operations import (
    apt,
    files,
    server,
    systemd,
    user,
    group,
)
from pyinfra.facts import server as server_facts
from pyinfra.facts import apt as apt_facts

# Get user from host data
user = host.data.get("user", "ubuntu")

# Install dependencies to add docker repository
apt.packages(
    name="Install Docker dependencies",
    packages=["apt-transport-https", "ca-certificates", "curl", "software-properties-common"],
    update=True,
    _sudo=True,
)

# Install keyrings
server.shell(
    name="Install keyrings",
    commands=["install -m 0755 -d /etc/apt/keyrings"],
    _sudo=True,
)

# Download Docker GPG key
files.download(
    name="Download Docker GPG key",
    src="https://download.docker.com/linux/ubuntu/gpg",
    dest="/etc/apt/keyrings/docker.asc",
    _sudo=True,
    mode="644",
)

# Get system architecture
arch = host.get_fact(server_facts.Arch)

# Get OS release
os_release = host.get_fact(server_facts.OsRelease).get("VERSION_CODENAME", "jammy")

# Add docker apt repository with signature
files.file(
    name="Add Docker apt repository",
    path="/etc/apt/sources.list.d/docker.list",
    content=f"deb [arch={arch} signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu {os_release} stable",
    _sudo=True,
    mode="644",
)

# Update apt cache
apt.update(
    name="Update apt cache",
    _sudo=True,
)

# Install docker-ce and dependencies
apt.packages(
    name="Install Docker packages",
    packages=[
        "docker-ce",
        "docker-ce-cli",
        "docker-ce-rootless-extras",
        "containerd.io",
        "docker-buildx-plugin",
        "docker-compose-plugin",
    ],
    _sudo=True,
)

# Create group docker
group.group(
    name="Create docker group",
    group_name="docker",
    _sudo=True,
)

# Add docker user to docker group
user.user(
    name=f"Add {user} to docker group",
    user=user,
    groups=["docker"],
    append=True,
    _sudo=True,
)

# Configure Docker daemon if enabled
if host.data.get("docker", {}).get("provision_daemon_json", False):
    # Create docker config directory
    files.directory(
        name="Create Docker config directory",
        path=host.data.get("docker", {}).get("daemon_config_folder", "/etc/docker"),
        _sudo=True,
    )
    
    # Copy daemon.json
    files.put(
        name="Copy Docker daemon config",
        src="files/daemon.json",
        dest=f"{host.data.get('docker', {}).get('daemon_config_folder', '/etc/docker')}/daemon.json",
        _sudo=True,
        mode="644",
    )
    
    # Restart docker service
    systemd.service(
        name="Restart Docker service",
        service="docker",
        running=True,
        restarted=True,
        enabled=True,
        _sudo=True,
    )

# Remove the dc calculator that we can use the docker compose alias
apt.packages(
    name="Remove conflicting dc package",
    packages=["dc"],
    present=False,
    _sudo=True,
)

# Add docker compose alias
files.line(
    name="Add docker compose alias",
    path=f"/home/{user}/.bash_aliases",
    line="alias dc='docker compose'",
    regex="^alias dc=",
    present=True,
    _sudo=True,
)

# Create docker metadata directory
files.directory(
    name="Create docker metadata directory",
    path=f"/home/{user}/.local/share/docker-image-usage",
    _sudo=True,
    user=user,
    group=user,
    mode="755",
)

# Create local bin directory
files.directory(
    name="Create local bin directory",
    path=f"/home/{user}/.local/bin",
    _sudo=True,
    user=user,
    group=user,
    mode="755",
)

# Copy docker events tracking script to local bin
files.put(
    name="Copy docker events tracking script",
    src="files/docker-events-track.sh",
    dest=f"/home/{user}/.local/bin/docker-events-track.sh",
    _sudo=True,
    user=user,
    group=user,
    mode="755",
)

# Create systemd user config directory
files.directory(
    name="Create systemd user config directory",
    path=f"/home/{user}/.config/systemd/user",
    _sudo=True,
    user=user,
    group=user,
    mode="755",
)

# Copy docker events tracking service file
files.put(
    name="Copy docker events tracking service file",
    src="files/docker-events-track.service",
    dest=f"/home/{user}/.config/systemd/user/docker-events-track.service",
    _sudo=True,
    user=user,
    group=user,
    mode="644",
)

# Reload systemd user daemon
systemd.daemon_reload(
    name="Reload systemd user daemon",
    user_mode=True,
    _sudo=True,
    _sudo_user=user,
)

# Enable docker events tracking service
systemd.service(
    name="Enable docker events tracking service",
    service="docker-events-track",
    running=True,
    enabled=True,
    user_mode=True,
    _sudo=True,
    _sudo_user=user,
)

# Copy docker cleanup script to cleanup scripts directory if cleanup_scripts is enabled
if host.data.get("cleanup_scripts", {}).get("dir"):
    files.put(
        name="Copy docker cleanup script",
        src="files/docker-cleanup.sh",
        dest=f"{host.data.get('cleanup_scripts', {}).get('dir')}/docker-cleanup",
        _sudo=True,
        mode="755",
    )