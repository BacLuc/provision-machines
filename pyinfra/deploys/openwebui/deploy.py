from operations.filesystem import dirname_of
from pyinfra import host
from pyinfra.operations import files, server, systemd
import io

user = host.data.get("user", "ubuntu")

if host.data.openwebui["enabled"]:
    compose_project_dir = host.data.openwebui["compose_project_dir"]

    server.shell(
        name="Create docker volume for openwebui",
        commands=["docker volume create open-webui"],
        _sudo=True,
    )

    files.directory(
        name="Create compose project directory",
        path=compose_project_dir,
        mode="755",
    )

    files.directory(
        name="Create searngx directory",
        path=f"{compose_project_dir}/searngx",
        mode="755",
    )

    files.put(
        name="Deploy docker-compose.yml",
        src=f"{dirname_of(__file__)}/files/docker-compose.yml",
        dest=f"{compose_project_dir}/docker-compose.yml",
        mode="644",
    )

    files.put(
        name="Deploy searngx limiter.toml",
        src=f"{dirname_of(__file__)}/files/searngx/limiter.toml",
        dest=f"{compose_project_dir}/searngx/limiter.toml",
        mode="644",
    )

    files.put(
        name="Deploy searngx settings.yml",
        src=f"{dirname_of(__file__)}/files/searngx/settings.yml",
        dest=f"{compose_project_dir}/searngx/settings.yml",
        mode="644",
    )

    files.put(
        name="Deploy systemd service file",
        src=io.StringIO(
            "[Unit]\n"
            "Description=OpenWebUI Service\n"
            "After=docker.service\n"
            "Requires=docker.service\n"
            "\n"
            "[Service]\n"
            "Type=oneshot\n"
            "RemainAfterExit=yes\n"
            f"WorkingDirectory={compose_project_dir}\n"
            "ExecStart=/usr/bin/docker compose up -d\n"
            "ExecStop=/usr/bin/docker compose down\n"
            "TimeoutStartSec=0\n"
            "\n"
            "[Install]\n"
            "WantedBy=multi-user.target\n"
        ),
        dest="/etc/systemd/system/openwebui.service",
        _sudo=True,
        mode="644",
    )
    systemd.service(
        name="Enable and start openwebui service",
        service="openwebui",
        running=True,
        enabled=True,
        restarted=True,
        _sudo=True,
    )
