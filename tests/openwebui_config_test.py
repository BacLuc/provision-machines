import re
from pathlib import Path

from jinja2 import Template

ROOT = Path(__file__).parents[1]
SETTINGS = ROOT / "deploys/openwebui/files/searngx/settings.yml.j2"
COMPOSE = ROOT / "deploys/openwebui/files/docker-compose.yml"
DEPLOY = ROOT / "deploys/openwebui/deploy.py"


def _engine_block(name: str) -> str:
    text = SETTINGS.read_text()
    match = re.search(rf"(?ms)^  - name: {re.escape(name)}\n(.*?)(?=^  - name:|\Z)", text)
    assert match
    return match.group(1)


def test_searxng_uses_valkey_for_limiter() -> None:
    settings = SETTINGS.read_text()
    compose = COMPOSE.read_text()

    assert re.search(r"(?ms)^  limiter: true$", settings)
    assert "url: valkey://valkey:6379/0" in settings
    assert "valkey/valkey:" in compose
    assert "condition: service_healthy" in compose


def test_brave_search_is_api_only_general_web_search() -> None:
    search = _engine_block("brave")
    assert "engine: braveapi" in search
    assert "categories: [general, web]" in search
    assert "paging: true" in search
    assert "api_key: {{ brave_api_key | tojson }}" in search
    assert not re.search(r"^  - name: brave\.(images|videos|news)$", SETTINGS.read_text(), re.MULTILINE)


def test_brave_image_support_and_secret_rendering() -> None:
    compose = COMPOSE.read_text()
    settings = SETTINGS.with_name("settings.yml.j2").read_text()
    assert "2026.2.16-8e824017d" in compose
    assert "braveapi" in settings
    assert "${BRAVE_API_KEY}" not in settings
    assert "BRAVE_API_KEY" not in compose
    assert "{{ brave_api_key | tojson }}" in settings
    assert "settings.yml.j2" in DEPLOY.read_text()

    rendered = Template(settings).render(brave_api_key="not-a-secret")
    assert 'api_key: "not-a-secret"' in rendered
    assert "brave_api_key" not in rendered


def test_synced_searxng_config_restarts_service() -> None:
    deploy = DEPLOY.read_text()
    docker_restart = deploy.split('name="Restart docker', 1)[1].split("systemd.service", 1)[0]
    service_restart = deploy.split('name="Enable and start openwebui service', 1)[1]
    assert "searngx_dir.changed" not in docker_restart
    assert "settings_file.changed" not in docker_restart
    assert "searngx_dir.changed" in service_restart
    assert "settings_file.changed" in service_restart
