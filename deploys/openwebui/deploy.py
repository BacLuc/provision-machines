import io
import json
import shlex
import sys

from pyinfra import host
from pyinfra.facts.files import Directory
from pyinfra.operations import files, server, systemd

from operations.filesystem import dirname_of
from operations.user import get_user_name

# renovate: datasource=docker depName=ghcr.io/api7/aisix
aisix_version = "1.4.0"

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

    searxng_files = files.sync(
        name="Copy searngx directory",
        src=f"{dirname_of(__file__)}/files/searngx",
        dest=f"{compose_project_dir}/searngx",
        mode="755",
        exclude="*/settings.yml",
    )

    with open(f"{dirname_of(__file__)}/files/searngx/settings.yml") as settings_template:
        settings = settings_template.read().replace(
            '"${BRAVE_API_KEY}"', json.dumps(host.data.openwebui["BRAVE_API_KEY"])
        )

    settings_file = files.put(
        name="Deploy searxng settings.yml",
        src=io.StringIO(settings),
        dest=f"{compose_project_dir}/searngx/settings.yml",
        user=user,
        group=user,
        mode="600",
        _sudo=True,
    )

    compose_file = files.put(
        name="Deploy docker-compose.yml",
        src=f"{dirname_of(__file__)}/files/docker-compose.yml",
        dest=f"{compose_project_dir}/docker-compose.yml",
        user=user,
        group=user,
        mode="644",
    )

    aisix_config_file = files.put(
        name="Deploy aisix config.yaml",
        src=f"{dirname_of(__file__)}/files/aisix-config.yaml",
        dest=f"{compose_project_dir}/aisix-config.yaml",
        user=user,
        group=user,
        mode="644",
    )

    aisix_resources_file = files.put(
        name="Deploy aisix resources.yaml",
        src=f"{dirname_of(__file__)}/files/aisix-resources.yaml",
        dest=f"{compose_project_dir}/aisix-resources.yaml",
        user=user,
        group=user,
        mode="644",
    )

    env_file = files.put(
        name="Deploy .env",
        src=io.StringIO(
            "\n".join(
                [
                    f"AISIX_VERSION={aisix_version}",
                    f"OPENCODE_API_KEY={host.data.openwebui['opencode_api_key']}",
                    f"OLLAMA_API_KEY={host.data.openwebui['ollama_api_key']}",
                    f"OPENWEBUI_CALLER_KEY={host.data.openwebui['openwebui_caller_key']}",
                    f"OPENCODE_BASE_URL={host.data.openwebui['opencode_base_url']}",
                    f"OLLAMA_BASE_URL={host.data.openwebui['ollama_base_url']}",
                    f"ZEN_MODEL_CHAT={host.data.openwebui['zen_model_chat']}",
                    f"OLLAMA_MODEL_CHAT={host.data.openwebui['ollama_model_chat']}",
                ]
                + [f"{k}={v}" for k, v in host.data.openwebui["extra_env"].items()]
            )
            + "\n"
        ),
        dest=f"{compose_project_dir}/.env",
        user=user,
        group=user,
        mode="600",
    )

    models_config_file = files.put(
        name="Deploy openwebui models config",
        src=io.StringIO(
            json.dumps(
                {
                    "model_map": host.data.openwebui["model_map"],
                    "base_url": "http://127.0.0.1:13307",
                    "default_models": host.data.openwebui["default_models"],
                }
            )
        ),
        dest=f"{compose_project_dir}/openwebui-models-config.json",
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

    server.shell(
        name="Restart docker before starting openwebui to ensure iptables chains exist",
        commands=["systemctl restart docker"],
        _sudo=True,
        _if=lambda: systemd_file.changed or compose_file.changed,
    )

    systemd.service(
        name="Enable and start openwebui service",
        service="openwebui",
        daemon_reload=True,
        enabled=True,
        restarted=True,
        _sudo=True,
        _if=lambda: (
            searxng_files.changed
            or settings_file.changed
            or systemd_file.changed
            or compose_file.changed
            or aisix_config_file.changed
            or aisix_resources_file.changed
            or env_file.changed
            or models_config_file.changed
        ),
    )

    server.shell(
        name="Reconcile openwebui models",
        commands=[
            f"{shlex.quote(sys.executable)} {shlex.quote(f'{dirname_of(__file__)}/../../scripts/update-openwebui-models.py')} --config {shlex.quote(f'{compose_project_dir}/openwebui-models-config.json')} --env-file {shlex.quote(f'{compose_project_dir}/.env')}"
        ],
        _if=lambda: (
            searxng_files.changed
            or settings_file.changed
            or systemd_file.changed
            or compose_file.changed
            or aisix_config_file.changed
            or aisix_resources_file.changed
            or env_file.changed
            or models_config_file.changed
        ),
    )
