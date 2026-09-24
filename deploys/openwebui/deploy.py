import io
import json
import re
import shlex
from typing import Any

from pyinfra import host
from pyinfra.facts.files import Directory
from pyinfra.operations import files, server, systemd

from operations.filesystem import dirname_of
from operations.user import get_user_name

# renovate: datasource=docker depName=ghcr.io/berriai/litellm
LITELLM_VERSION = "v1.102.1"

user = get_user_name()


def _resolve_env_refs(value: str, values: dict[str, str]) -> str:
    for ref in re.findall(r"\$\{([^}]+)\}", value):
        if ref in values:
            value = value.replace("${" + ref + "}", values[ref])
    return value


def _render_env(openwebui: dict[str, Any]) -> str:
    values: dict[str, str] = {
        "BRAVE_API_KEY": str(openwebui.get("BRAVE_API_KEY", "")),
        "LITELLM_MASTER_KEY": str(openwebui.get("LITELLM_MASTER_KEY", "")),
        "OPENCODE_GO_API_KEY": str(openwebui.get("OPENCODE_GO_API_KEY", "")),
        "ZEN_API_BASE": str(openwebui.get("zen", {}).get("base_url", "")),
        "OLLAMA_API_BASE": str(openwebui.get("ollama", {}).get("base_url", "")),
        "OPENWEBUI_ADMIN_API_KEY": str(openwebui.get("OPENWEBUI_ADMIN_API_KEY", "")),
    }
    extra_env = openwebui.get("extra_env", {})
    if isinstance(extra_env, dict):
        for key, value in extra_env.items():
            values[str(key)] = str(value)
    for key, value in values.items():
        values[key] = _resolve_env_refs(value, values)
    return "".join(f"{key}={value}\n" for key, value in values.items())


def _render_litellm_config(template: str, openwebui: dict[str, Any]) -> str:
    zen_models = openwebui.get("zen", {}).get("models", {})
    replacements = {
        "__ZEN_CHAT_MODEL__": str(zen_models.get("chat", "")),
        "__ZEN_CHAT_THINKING_MODEL__": str(zen_models.get("chat_thinking", "")),
        "__ZEN_WEB_RESEARCH_MODEL__": str(zen_models.get("web_research", "")),
        "__ZEN_TRANSLATE_DE_MODEL__": str(zen_models.get("translate_de", "")),
        "__ZEN_TRANSLATE_EN_MODEL__": str(zen_models.get("translate_en", "")),
        "__ZEN_FIX_GRAMMAR_EN_MODEL__": str(zen_models.get("fix_grammar_en", "")),
        "__ZEN_FIX_GRAMMAR_DE_MODEL__": str(zen_models.get("fix_grammar_de", "")),
        "__ZEN_LINUX_CLI_MODEL__": str(zen_models.get("linux_cli", "")),
        "__OLLAMA_MODEL__": str(openwebui.get("ollama", {}).get("model", "")),
    }
    for placeholder, value in replacements.items():
        template = template.replace(placeholder, value)
    return template


def _render_models_json(openwebui: dict[str, Any]) -> dict[str, Any]:
    return {
        "default_models": openwebui.get("default_models", []),
        "model_map": openwebui.get("model_map", {}),
    }


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

    with open(f"{dirname_of(__file__)}/files/docker-compose.yml") as compose_template:
        compose = compose_template.read().replace("__LITELLM_VERSION__", LITELLM_VERSION)

    compose_file = files.put(
        name="Deploy docker-compose.yml",
        src=io.StringIO(compose),
        dest=f"{compose_project_dir}/docker-compose.yml",
        user=user,
        group=user,
        mode="644",
    )

    env_file = files.put(
        name="Deploy .env",
        src=io.StringIO(_render_env(host.data.openwebui)),
        dest=f"{compose_project_dir}/.env",
        user=user,
        group=user,
        mode="600",
    )

    with open(f"{dirname_of(__file__)}/files/litellm-config.yaml") as config_template:
        litellm_config = _render_litellm_config(config_template.read(), host.data.openwebui)

    litellm_config_file = files.put(
        name="Deploy litellm-config.yaml",
        src=io.StringIO(litellm_config),
        dest=f"{compose_project_dir}/litellm-config.yaml",
        user=user,
        group=user,
        mode="644",
    )

    models_json_file = files.put(
        name="Deploy openwebui-models.json",
        src=io.StringIO(json.dumps(_render_models_json(host.data.openwebui), indent=2) + "\n"),
        dest=f"{compose_project_dir}/openwebui-models.json",
        user=user,
        group=user,
        mode="644",
    )

    sync_script_file = files.put(
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
            or litellm_config_file.changed
        ),
    )

    server.shell(
        name="Reconcile OpenWebUI models",
        commands=[
            f"{shlex.quote(f'{compose_project_dir}/update-openwebui-models.py')} "
            f"--config {shlex.quote(f'{compose_project_dir}/openwebui-models.json')} "
            f"--router-config {shlex.quote(f'{compose_project_dir}/litellm-config.yaml')} "
            f"--env-file {shlex.quote(f'{compose_project_dir}/.env')} "
            f"--url http://127.0.0.1:13307"
        ],
    )
