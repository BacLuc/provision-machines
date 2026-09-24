import importlib.util
import os
import re
from pathlib import Path
from typing import Any, cast

_REPO_ROOT = Path(__file__).resolve().parent.parent
_LITELLM_CONFIG = _REPO_ROOT / "deploys" / "openwebui" / "files" / "litellm-config.yaml"
_COMPOSE = _REPO_ROOT / "deploys" / "openwebui" / "files" / "docker-compose.yml"

_LITELLM_ENV_VARS = [
    "LITELLM_MASTER_KEY",
    "OPENCODE_GO_API_KEY",
    "ZEN_API_BASE",
    "OLLAMA_API_BASE",
]

_OPENWEBUI_ENV_VARS = [
    "WEBUI_AUTH",
    "DATABASE_ENABLE_SESSION_SHARING",
    "OPENWEBUI_ADMIN_API_KEY",
    "ENABLE_OPENAI_API",
    "OPENAI_API_BASE_URL",
    "OPENAI_API_KEYS",
    "DEFAULT_MODELS",
]


def _load_openwebui() -> dict[str, Any]:
    os.environ["CI"] = ""
    spec = importlib.util.spec_from_file_location("group_data_all_stack", _REPO_ROOT / "group_data" / "all.py")
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return cast(dict[str, Any], mod.openwebui)


def _litellm_entries() -> list[str]:
    text = _LITELLM_CONFIG.read_text()
    return re.split(r"\n  - model_name: ", text)[1:]


def _service_block(text: str, name: str) -> str:
    match = re.search(rf"^  {name}:$.*?(?=^  [a-z-]+:$|^volumes:)", text, re.MULTILINE | re.DOTALL)
    assert match is not None, f"service {name} not found"
    return match.group(0)


def _env_vars(block: str) -> list[str]:
    return re.findall(r'^      - "([A-Z_]+)=', block, re.MULTILINE)


def test_litellm_config_entries_match_model_map_and_ollama() -> None:
    openwebui = _load_openwebui()
    entries = _litellm_entries()
    router_ids = {entry.splitlines()[0].strip() for entry in entries}
    expected = set(openwebui["model_map"].values()) | {"router-ollama"}
    assert router_ids == expected


def test_litellm_params_reference_env_vars() -> None:
    for entry in _litellm_entries():
        params = entry.split("litellm_params:")[1]
        for key in ("api_base", "api_key"):
            line = next(
                (line for line in params.splitlines() if line.strip().startswith(f"{key}:")),
                None,
            )
            # api_key is optional (ollama needs none); when present it must
            # come from the environment, never from the template.
            if line is not None:
                assert line.strip().startswith(f"{key}: os.environ/"), line


def test_litellm_router_settings() -> None:
    text = _LITELLM_CONFIG.read_text()
    assert "routing_strategy: simple-shuffle" in text
    assert "num_retries: 2" in text
    assert "timeout: 30" in text
    assert "allowed_fails: 3" in text
    assert "cooldown_time: 30" in text


def test_litellm_every_zen_router_has_ollama_fallback() -> None:
    openwebui = _load_openwebui()
    text = _LITELLM_CONFIG.read_text()
    for router_id in openwebui["model_map"].values():
        assert f"- {router_id}: [router-ollama]" in text, router_id


def test_litellm_general_settings_master_key() -> None:
    assert "master_key: os.environ/LITELLM_MASTER_KEY" in _LITELLM_CONFIG.read_text()


def test_compose_litellm_service() -> None:
    text = _COMPOSE.read_text()
    block = _service_block(text, "litellm")
    assert 'image: "ghcr.io/berriai/litellm:__LITELLM_VERSION__"' in block
    assert "ports:" not in block
    assert '- "host.docker.internal:host-gateway"' in block
    assert '"./litellm-config.yaml:/app/config.yaml:ro"' in block
    assert 'command: ["--config", "/app/config.yaml"]' in block
    assert 'restart: "unless-stopped"' in block
    assert _env_vars(block) == _LITELLM_ENV_VARS


def test_compose_openwebui_env() -> None:
    block = _service_block(_COMPOSE.read_text(), "open-webui")
    assert "WEBUI_AUTH=False" in block
    assert "DATABASE_ENABLE_SESSION_SHARING=True" in block
    for var in _OPENWEBUI_ENV_VARS:
        if var in ("WEBUI_AUTH", "DATABASE_ENABLE_SESSION_SHARING"):
            continue
        assert f"${{{var}}}" in block


def test_compose_searxng_unchanged() -> None:
    block = _service_block(_COMPOSE.read_text(), "searxng")
    assert "ghcr.io/searxng/searxng:2026.2.16-8e824017d" in block
    assert "127.0.0.1:13308:8080" in block
