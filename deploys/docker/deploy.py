import io

from pyinfra.facts import server as server_facts

from operations.filesystem import dirname_of
from operations.user import get_user_name
from pyinfra import host
from pyinfra.operations import (
    apt,
    files,
    server,
)

user = get_user_name()

if host.data.docker["enabled"]:
    apt.packages(
        name="Install Docker dependencies",
        packages=["apt-transport-https", "ca-certificates", "curl", "software-properties-common"],
        update=True,
        _sudo=True,
    )

    server.shell(
        name="Install keyrings",
        commands=["install -m 0755 -d /etc/apt/keyrings"],
        _sudo=True,
    )

    files.download(
        name="Download Docker GPG key",
        src="https://download.docker.com/linux/ubuntu/gpg",
        dest="/etc/apt/keyrings/docker.asc",
        _sudo=True,
        mode="644",
    )

    arch = "amd64"

    os_release = host.get_fact(server_facts.OsRelease)["version_codename"]
    if os_release is None:
        raise ValueError("OS release not found, cannot proceed with Docker installation")

    files.put(
        name="Add Docker apt repository",
        dest="/etc/apt/sources.list.d/docker.list",
        src=io.StringIO(
            f"deb [arch={arch} signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu {os_release} stable"
        ),
        _sudo=True,
        mode="644",
    )

    apt.update(
        name="Update apt cache",
        _sudo=True,
    )

    apt.packages(
        name="Install Docker packages",
        packages=[
            "docker-buildx-plugin",
            "docker-ce",
            "docker-ce-cli",
            "docker-ce-rootless-extras",
            "containerd.io",
            "docker-compose-plugin",
        ],
        _sudo=True,
    )

    server.group(
        name="Create docker group",
        group="docker",
        _sudo=True,
    )

    server.user(
        name=f"Add {user} to docker group",
        user=user,
        groups=["docker"],
        append=True,
        _sudo=True,
    )

    if host.data.docker["provision_daemon_json"]:
        files.directory(
            name="Create Docker config directory",
            path=host.data.get("docker", {}).get("daemon_config_folder", "/etc/docker"),
            _sudo=True,
        )

        daemon_json_file = files.put(
            name="Copy Docker daemon config",
            src=f"{dirname_of(__file__)}/files/daemon.json",
            dest=f"{host.data.docker['daemon_config_folder']}/daemon.json",
            _sudo=True,
            mode="644",
        )

        server.shell(
            name="Restart Docker service",
            commands=["systemctl restart docker 2>/dev/null || true"],
            _sudo=True,
            _if=lambda: daemon_json_file.changed,
        )

    apt.packages(
        name="Remove conflicting dc package",
        packages=["dc"],
        present=False,
        _sudo=True,
    )

    files.line(
        name="Add docker compose alias",
        path=f"/home/{user}/.bash_aliases",
        line="^alias dc=",
        replace="alias dc='docker compose'",
        present=True,
    )

    files.directory(
        name="Create docker metadata directory",
        path=f"/home/{user}/.local/share/docker-image-usage",
        user=user,
        group=user,
        mode="755",
    )

    files.directory(
        name="Create local bin directory",
        path=f"/home/{user}/.local/bin",
        user=user,
        group=user,
        mode="755",
    )

    files.put(
        name="Copy docker events tracking script",
        src=f"{dirname_of(__file__)}/files/docker-events-track.sh",
        dest=f"/home/{user}/.local/bin/docker-events-track.sh",
        user=user,
        group=user,
        mode="755",
    )

    files.directory(
        name="Create systemd user config directory",
        path=f"/home/{user}/.config/systemd/user",
        user=user,
        group=user,
        mode="755",
    )

    files.put(
        name="Copy docker events tracking service file",
        src=f"{dirname_of(__file__)}/files/docker-events-track.service",
        dest=f"/home/{user}/.config/systemd/user/docker-events-track.service",
        user=user,
        group=user,
        mode="644",
    )

    server.shell(
        name="Reload systemd user daemon and enable docker events service",
        commands=[
            "systemctl --user daemon-reload 2>/dev/null || true",
            "systemctl --user enable --now docker-events-track 2>/dev/null || true",
        ],
    )

    if host.data.cleanup_scripts["dir"]:
        files.put(
            name="Copy docker cleanup script",
            src=f"{dirname_of(__file__)}/files/docker-cleanup.sh",
            dest=f"{host.data.cleanup_scripts['dir']}/docker-cleanup",
            _sudo=True,
            mode="755",
        )
