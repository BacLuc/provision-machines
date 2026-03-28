"""Docker runtime environment setup and configuration."""

import os
from io import StringIO

from pyinfra.api.deploy import deploy
from pyinfra.context import host
from pyinfra.facts.server import Arch, LinuxDistribution, Which
from pyinfra.facts.systemd import SystemdStatus
from pyinfra.operations import apt, files, server, systemd


def _parse_bool(value):
    """Parse boolean value from string or other type."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "on")
    return bool(value)


@deploy("Docker")
def configure_docker(
    user=None,
    home=None,
    enable_daemon_config=True,
    daemon_config_folder="/etc/docker",
    enable_compose_alias=True,
    _sudo=None,
    **kwargs,
):
    """Setup Docker CE runtime environment."""
    # Check if enabled
    if not _parse_bool(host.data.get("enable_docker", False)):
        return

    # Get user/home from host.data if not provided
    if user is None:
        user = host.data.get("user") or os.environ.get("USER", "vscode")
    if home is None:
        home = f"/home/{user}"

    # Install dependencies to add docker repository
    apt.packages(
        name="Install Docker repository dependencies",
        packages=[
            "apt-transport-https",
            "ca-certificates",
            "curl",
            "software-properties-common",
        ],
        update=True,
    )

    # Install keyrings directory
    server.shell(
        name="Create keyrings directory",
        commands=["install -m 0755 -d /etc/apt/keyrings"],
    )

    # Download Docker GPG key
    files.download(
        name="Download Docker GPG key",
        src="https://download.docker.com/linux/ubuntu/gpg",
        dest="/etc/apt/keyrings/docker.asc",
        mode="644",
    )

    # Get system architecture using facts
    arch = host.get_fact(Arch)
    # Convert x86_64 to amd64 for Docker repository
    if arch == "x86_64":
        arch = "amd64"

    # Get OS release codename using facts
    linux_dist = host.get_fact(LinuxDistribution)
    release = linux_dist.get("release_meta", {}).get("CODENAME", "noble")

    docker_repo_content = f"deb [arch={arch} signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu {release} stable\n"

    files.put(
        name="Add Docker apt repository",
        src=StringIO(docker_repo_content),
        dest="/etc/apt/sources.list.d/docker.list",
        mode="644",
    )

    # Update apt cache
    apt.update(
        name="Update apt cache after adding Docker repository",
    )

    # Remove conflicting moby-tini package if it exists (conflicts with docker-ce)
    apt.packages(
        name="Remove conflicting moby-tini package",
        packages=["moby-tini"],
        present=False,
    )

    # Install Docker CE and dependencies
    apt.packages(
        name="Install Docker CE and dependencies",
        packages=[
            "docker-ce",
            "docker-ce-cli",
            "docker-ce-rootless-extras",
            "containerd.io",
            "docker-buildx-plugin",
            "docker-compose-plugin",
        ],
        update=True,
    )

    # Create docker group
    server.group(
        name="Create docker group",
        group="docker",
    )

    # Add user to docker group
    if user:
        server.shell(
            name=f"Add {user} to docker group",
            commands=[f"usermod -aG docker {user}"],
        )

    # Configure Docker daemon if enabled
    if enable_daemon_config:
        daemon_config = """{
  "bip": "172.28.0.1/18",
  "default-address-pools": [
    {
      "base": "172.28.64.0/18",
      "size": 24
    }
  ],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "5"
  }
}
"""
        files.put(
            name="Add Docker daemon configuration",
            src=StringIO(daemon_config),
            dest=f"{daemon_config_folder}/daemon.json",
            mode="644",
        )

        # Check if systemd is available and working
        # First check if systemctl command exists
        systemctl_exists = host.get_fact(Which, command="systemctl")

        if systemctl_exists:
            # Try to get systemd status to verify it's working
            try:
                systemd_status = host.get_fact(SystemdStatus, services=["docker.service"])
                # Check if systemd is actually working by checking if docker service is recognized
                # systemd_status can be a dict or boolean depending on the state
                if isinstance(systemd_status, dict):
                    docker_service = systemd_status.get("docker.service", {})
                    if isinstance(docker_service, dict) and docker_service.get("SubState") != "failed":
                        # Restart docker service to apply daemon configuration
                        systemd.service(
                            name="Restart Docker service",
                            service="docker",
                            running=True,
                            restarted=True,
                            enabled=True,
                        )
                        # Exit early since we handled systemd
                        return
                raise Exception("Systemd docker service not working")
            except Exception:
                pass

        # If systemd is not available or not working (e.g., in container), start docker directly
        server.shell(
            name="Start Docker service (no systemd)",
            commands=["dockerd > /var/log/dockerd.log 2>&1 &"],
        )

    # Remove conflicting dc package if it exists
    apt.packages(
        name="Remove conflicting dc package",
        packages=["dc"],
        present=False,
    )

    # Add docker compose alias if enabled
    if enable_compose_alias and home:
        bash_aliases_path = os.path.join(home, ".bash_aliases")
        files.line(
            name="Add docker compose alias",
            path=bash_aliases_path,
            line="alias dc='docker compose'",
            ensure_newline=True,
        )
