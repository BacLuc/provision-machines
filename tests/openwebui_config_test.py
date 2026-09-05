import re
from pathlib import Path

ROOT = Path(__file__).parents[1]
SETTINGS = ROOT / "deploys/openwebui/files/searngx/settings.yml"
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
    assert "paging: false" in search

    for name, category in (("brave.images", "images"), ("brave.videos", "videos"), ("brave.news", "news")):
        block = _engine_block(name)
        assert f"brave_category: {category}" in block
        assert "disabled: true" in block


def test_synced_searxng_config_restarts_service() -> None:
    deploy = DEPLOY.read_text()
    assert "searngx_dir.changed" in deploy
