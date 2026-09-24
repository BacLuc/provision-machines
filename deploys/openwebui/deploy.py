import io
import json

from pyinfra import host
from pyinfra.facts.files import Directory
from pyinfra.operations import files, server, systemd

from operations.filesystem import dirname_of
from operations.user import get_user_name

# renovate: datasource=docker depName=ghcr.io/berriai/litellm
litellm_version = "1.102.1"

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

    extra_env = dict(host.data.openwebui["extra_env"])
    extra_env["DEFAULT_MODELS"] = ",".join(host.data.openwebui["default_models"])
    extra_env["OPENAI_API_KEYS"] = host.data.openwebui["LITELLM_MASTER_KEY"]
    env_block = "\n".join(f'      - "{k}={v}"' for k, v in extra_env.items())
    with open(f"{dirname_of(__file__)}/files/docker-compose.yml") as compose_template:
        compose_content = compose_template.read().replace('      - "__OPENWEBUI_EXTRA_ENV__"', env_block)

    compose_file = files.put(
        name="Deploy docker-compose.yml",
        src=io.StringIO(compose_content),
        dest=f"{compose_project_dir}/docker-compose.yml",
        user=user,
        group=user,
        mode="644",
    )

    litellm_config_file = files.put(
        name="Deploy litellm config",
        src=f"{dirname_of(__file__)}/files/litellm-config.yaml",
        dest=f"{compose_project_dir}/litellm-config.yaml",
        user=user,
        group=user,
        mode="644",
    )

    env_file = files.put(
        name="Deploy .env",
        src=io.StringIO(
            "\n".join(
                [
                    f"LITELLM_VERSION={litellm_version}",
                    f"LITELLM_MASTER_KEY={host.data.openwebui['LITELLM_MASTER_KEY']}",
                    f"OPENCODE_GO_API_KEY={host.data.openwebui['OPENCODE_GO_API_KEY']}",
                    f"OPENCODE_GO_2_API_KEY={host.data.openwebui['OPENCODE_GO_2_API_KEY']}",
                    "",
                ]
            )
        ),
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
            or litellm_config_file.changed
            or env_file.changed
        ),
    )

    models_config_file = files.put(
        name="Deploy openwebui models config",
        src=io.StringIO(
            json.dumps(
                {
                    "default_models": host.data.openwebui["default_models"],
                    "model_map": host.data.openwebui["model_map"],
                },
                indent=2,
            )
        ),
        dest=f"{compose_project_dir}/openwebui-models.json",
        user=user,
        group=user,
        mode="644",
    )

    sync_script_file = files.put(
        name="Deploy openwebui model sync script",
        src=f"{dirname_of(__file__)}/../../scripts/update-openwebui-models.py",
        dest=f"{compose_project_dir}/update-openwebui-models.py",
        user=user,
        group=user,
        mode="755",
    )

    server.shell(
        name="Reconcile OpenWebUI models",
        commands=[
            f"python3 {compose_project_dir}/update-openwebui-models.py "
            f"--url http://127.0.0.1:13307 "
            f"--config {compose_project_dir}/openwebui-models.json "
            f"--env-file {compose_project_dir}/.env"
        ],
        _if=lambda: (
            systemd_file.changed
            or compose_file.changed
            or litellm_config_file.changed
            or env_file.changed
            or models_config_file.changed
            or sync_script_file.changed
        ),
    )
