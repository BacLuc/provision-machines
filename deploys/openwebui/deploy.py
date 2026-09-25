import io
import json
import shlex

from pyinfra import host
from pyinfra.facts.files import Directory
from pyinfra.operations import files, server, systemd

from operations.filesystem import dirname_of
from operations.user import get_user_name

# renovate: datasource=docker depName=ghcr.io/api7/aisix
AISIX_VERSION = "1.4.0"

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
        dest=f"{compose_project_dir}/searxng/settings.yml",
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

    env_values: dict[str, str] = {"AISIX_VERSION": AISIX_VERSION}
    for key, value in host.data.openwebui["extra_env"].items():
        env_values[key] = str(value)
    for key in ("ZEN_API_KEY", "OLLAMA_API_KEY", "OPENWEBUI_CALLER_KEY", "OPENWEBUI_ADMIN_API_KEY"):
        env_values[key] = str(host.data.openwebui[key])
    env_values["ZEN_API_BASE"] = str(host.data.openwebui["zen"]["base_url"])
    env_values["OLLAMA_API_BASE"] = str(host.data.openwebui["ollama"]["base_url"])
    for family, model in host.data.openwebui["zen"]["models"].items():
        env_values[f"ZEN_{family.upper()}_MODEL"] = str(model)
    for family, model in host.data.openwebui["ollama"]["models"].items():
        env_values[f"OLLAMA_{family.upper()}_MODEL"] = str(model)
    if any("\n" in value for value in env_values.values()):
        raise ValueError("openwebui .env values must not contain newlines")
    env_file = files.put(
        name="Deploy .env",
        src=io.StringIO("".join(f"{key}={value}\n" for key, value in env_values.items())),
        dest=f"{compose_project_dir}/.env",
        user=user,
        group=user,
        mode="600",
        _sudo=True,
    )

    aisix_config_file = files.put(
        name="Deploy aisix-config.yaml",
        src=f"{dirname_of(__file__)}/files/aisix-config.yaml",
        dest=f"{compose_project_dir}/{host.data.openwebui['router_config_path']}",
        user=user,
        group=user,
        mode="644",
    )

    resources_file = files.put(
        name="Deploy resources.yaml",
        src=f"{dirname_of(__file__)}/files/resources.yaml",
        dest=f"{compose_project_dir}/{host.data.openwebui['router_resources_path']}",
        user=user,
        group=user,
        mode="644",
    )

    models_manifest_file = files.put(
        name="Deploy openwebui-models.json",
        src=io.StringIO(
            json.dumps(
                {
                    "default_models": host.data.openwebui["default_models"],
                    "model_map": host.data.openwebui["model_map"],
                    "presets": host.data.openwebui["presets"],
                },
                indent=2,
            )
            + "\n"
        ),
        dest=f"{compose_project_dir}/openwebui-models.json",
        user=user,
        group=user,
        mode="644",
    )

    reconciler_file = files.put(
        name="Deploy update-openwebui-models.py",
        src=f"{dirname_of(__file__)}/../../scripts/update-openwebui-models.py",
        dest=f"{compose_project_dir}/update-openwebui-models.py",
        user=user,
        group=user,
        mode="755",
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
            or env_file.changed
            or aisix_config_file.changed
            or resources_file.changed
            or models_manifest_file.changed
            or reconciler_file.changed
        ),
    )

    server.shell(
        name="Reconcile OpenWebUI model presets",
        commands=[
            "systemctl start openwebui.service && docker kill --signal=HUP aisix && python3 "
            + " ".join(
                [
                    shlex.quote(f"{compose_project_dir}/update-openwebui-models.py"),
                    "--url",
                    shlex.quote("http://127.0.0.1:13307"),
                    "--manifest",
                    shlex.quote(f"{compose_project_dir}/openwebui-models.json"),
                    "--resources",
                    shlex.quote(f"{compose_project_dir}/{host.data.openwebui['router_resources_path']}"),
                    "--env-file",
                    shlex.quote(f"{compose_project_dir}/.env"),
                ]
            )
        ],
        _sudo=True,
    )
