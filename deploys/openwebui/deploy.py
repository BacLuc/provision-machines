import io
import json
import shlex

from pyinfra import host
from pyinfra.facts.files import Directory
from pyinfra.operations import files, server, systemd

from operations.filesystem import dirname_of
from operations.user import get_user_name

user = get_user_name()

# renovate: datasource=docker depName=ghcr.io/berriai/litellm
LITELLM_VERSION = "1.102.1"

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

    litellm_config_file = files.put(
        name="Deploy litellm-config.yaml",
        src=f"{dirname_of(__file__)}/files/litellm-config.yaml",
        dest=f"{compose_project_dir}/litellm-config.yaml",
        user=user,
        group=user,
        mode="644",
    )

    openwebui = host.data.openwebui

    def _resolve_env(value: str) -> str:
        return value.replace("${LITELLM_MASTER_KEY}", str(openwebui["LITELLM_MASTER_KEY"])).replace(
            "${OPENAI_COMPATIBLE_BASE_URL}", str(openwebui["openai_compatible_base_url"])
        )

    env_lines = [
        f"BRAVE_API_KEY={openwebui['BRAVE_API_KEY']}",
        f"OPENCODE_GO_API_KEY={openwebui['OPENCODE_GO_API_KEY']}",
        f"LITELLM_MASTER_KEY={openwebui['LITELLM_MASTER_KEY']}",
        f"OPENWEBUI_ADMIN_API_KEY={openwebui['OPENWEBUI_ADMIN_API_KEY']}",
        f"OLLAMA_API_KEY={openwebui.get('OLLAMA_API_KEY', 'ollama')}",
        f"ZEN_API_BASE={openwebui['zen']['base_url']}",
        f"OLLAMA_API_BASE={openwebui['ollama']['base_url']}",
        f"OLLAMA_MODEL=ollama/{openwebui['ollama']['model']}",
        f"LITELLM_VERSION={LITELLM_VERSION}",
    ]
    for preset in openwebui["default_models"]:
        env_lines.append(f"ZEN_{preset.upper()}_MODEL={openwebui['zen']['models'][preset]}")
    for key, value in openwebui["extra_env"].items():
        env_lines.append(f"{key}={_resolve_env(value)}")

    env_file = files.put(
        name="Deploy .env file",
        src=io.StringIO("\n".join(env_lines) + "\n"),
        dest=f"{compose_project_dir}/.env",
        user=user,
        group=user,
        mode="600",
        _sudo=True,
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
        _if=lambda: systemd_file.changed or compose_file.changed or env_file.changed or litellm_config_file.changed,
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
            or litellm_config_file.changed
        ),
    )

    reconcile_args = json.dumps(
        {
            "base_url": "http://127.0.0.1:13307",
            "admin_api_key": openwebui["OPENWEBUI_ADMIN_API_KEY"],
            "config_path": f"{compose_project_dir}/litellm-config.yaml",
            "models": [
                {"preset_id": preset, "router_model_id": router_id}
                for preset, router_id in openwebui["model_map"].items()
            ],
        }
    )
    args_file = files.put(
        name="Deploy openwebui-models args file",
        src=io.StringIO(reconcile_args),
        dest=f"{compose_project_dir}/openwebui-models-args.json",
        user=user,
        group=user,
        mode="600",
        _sudo=True,
    )

    reconcile_script_file = files.put(
        name="Deploy update-openwebui-models.py",
        src=f"{dirname_of(__file__)}/../../scripts/update-openwebui-models.py",
        dest=f"{compose_project_dir}/update-openwebui-models.py",
        user=user,
        group=user,
        mode="755",
    )

    server.shell(
        name="Reconcile OpenWebUI models",
        commands=[
            f"cd {shlex.quote(compose_project_dir)} && "
            f"python3 {shlex.quote(compose_project_dir + '/update-openwebui-models.py')} "
            f"--args-file {shlex.quote(compose_project_dir + '/openwebui-models-args.json')}"
        ],
        _sudo=True,
        _if=lambda: (
            args_file.changed
            or reconcile_script_file.changed
            or systemd_file.changed
            or compose_file.changed
            or env_file.changed
            or litellm_config_file.changed
        ),
    )
