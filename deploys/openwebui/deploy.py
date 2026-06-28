import io

from pyinfra.facts.files import Directory

from operations.filesystem import dirname_of
from operations.user import get_user_name
from pyinfra import host
from pyinfra.operations import files, server, systemd

user = get_user_name()

if host.data.openwebui["enabled"]:
    compose_project_dir = host.data.openwebui.get("compose_project_dir") or f"/home/{user}/openwebui"

    server.shell(
        name="Create docker volume",
        commands=["docker volume create open-webui"],
        _sudo=True,
        _if=lambda: host.get_fact(Directory, "/var/lib/docker/volumes/open-webui") is None,
    )

    files.directory(
        name="Create compose project directory",
        path=compose_project_dir,
        user=user,
        group=user,
        mode="755",
    )

    files.sync(
        name="Copy searngx directory",
        src=f"{dirname_of(__file__)}/files/searngx",
        dest=f"{compose_project_dir}/searngx",
        mode="755",
    )

    compose_file = files.put(
        name="Deploy docker-compose.yml",
        src=f"{dirname_of(__file__)}/files/docker-compose.yml",
        dest=f"{compose_project_dir}/docker-compose.yml",
        user=user,
        group=user,
        mode="644",
    )

    systemd_file = files.put(
        name="Deploy systemd service file",
        src=io.StringIO(
            f"""[Unit]
Description=OpenWebUI Service
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory={compose_project_dir}
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
"""
        ),
        dest="/etc/systemd/system/openwebui.service",
        _sudo=True,
        mode="644",
    )

    systemd.service(
        name="Enable and start openwebui service",
        service="openwebui",
        daemon_reload=True,
        enabled=True,
        restarted=True,
        _sudo=True,
        _if=lambda: systemd_file.changed or compose_file.changed,
    )
