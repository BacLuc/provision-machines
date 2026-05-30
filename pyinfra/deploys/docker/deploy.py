from operations.filesystem import dirname_of
from pyinfra import host
from pyinfra.operations import (
    apt,
    files,
    server,
    systemd,
)
from pyinfra.facts import server as server_facts
from pyinfra.facts import apt as apt_facts
import io

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
files.put(
    name="Add Docker apt repository",
    dest="/etc/apt/sources.list.d/docker.list",
    src=io.StringIO(f"deb [arch={arch} signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu {os_release} stable"),
    _sudo=True,
    mode="644",
)

# Update apt cache
apt.update(
    name="Update apt cache",
    _sudo=True,
)

# Install docker-ce and dependencies
server.shell(
    name="Install Docker packages",
    commands=["which docker > /dev/null 2>&1 || apt-get install -y docker-ce docker-ce-cli docker-ce-rootless-extras containerd.io docker-buildx-plugin docker-compose-plugin"],
    _sudo=True,
)

# Create group docker
server.group(
    name="Create docker group",
    group="docker",
    _sudo=True,
)

# Add docker user to docker group
server.user(
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
        src=f"{dirname_of(__file__)}/files/daemon.json",
        dest=f"{host.data.get('docker', {}).get('daemon_config_folder', '/etc/docker')}/daemon.json",
        _sudo=True,
        mode="644",
    )
    
    # Restart docker service
    server.shell(
        name="Restart Docker service",
        commands=["systemctl restart docker 2>/dev/null || true"],
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
    replace="^alias dc=",
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
    src=f"{dirname_of(__file__)}/files/docker-events-track.sh",
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
    src=f"{dirname_of(__file__)}/files/docker-events-track.service",
    dest=f"/home/{user}/.config/systemd/user/docker-events-track.service",
    _sudo=True,
    user=user,
    group=user,
    mode="644",
)

# Reload systemd user daemon
server.shell(
    name="Reload systemd user daemon and enable docker events service",
    commands=[
        f"systemctl --user daemon-reload 2>/dev/null || true",
        f"systemctl --user enable --now docker-events-track 2>/dev/null || true",
    ],
)

# Copy docker cleanup script to cleanup scripts directory if cleanup_scripts is enabled
if host.data.get("cleanup_scripts", {}).get("dir"):
    files.put(
        name="Copy docker cleanup script",
        src=f"{dirname_of(__file__)}/files/docker-cleanup.sh",
        dest=f"{host.data.get('cleanup_scripts', {}).get('dir')}/docker-cleanup",
        _sudo=True,
        mode="755",
    )