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
    "OLLAMA_API_KEY",
    "OLLAMA_API_BASE",
    "ZEN_API_BASE",
    "ZEN_CHAT_MODEL",
    "ZEN_CHAT_THINKING_MODEL",
    "ZEN_WEB_RESEARCH_MODEL",
    "ZEN_TRANSLATE_DE_MODEL",
    "ZEN_TRANSLATE_EN_MODEL",
    "ZEN_FIX_GRAMMAR_EN_MODEL",
    "ZEN_FIX_GRAMMAR_DE_MODEL",
    "ZEN_LINUX_CLI_MODEL",
    "OLLAMA_MODEL",
]

_OPENWEBUI_ENV_VARS = [
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


def test_litellm_config_has_16_entries_matching_model_map() -> None:
    entries = _litellm_entries()
    assert len(entries) == 16
    router_ids = {entry.splitlines()[0].strip() for entry in entries}
    assert router_ids == set(_load_openwebui()["model_map"].values())


def test_litellm_params_reference_env_vars() -> None:
    for entry in _litellm_entries():
        params = entry.split("litellm_params:")[1]
        for key in ("model", "api_base", "api_key"):
            line = next(line for line in params.splitlines() if line.strip().startswith(f"{key}:"))
            assert line.strip().startswith(f"{key}: os.environ/"), line


def test_litellm_each_router_has_order_1_and_2() -> None:
    orders_by_router: dict[str, list[str]] = {}
    for entry in _litellm_entries():
        router_id = entry.splitlines()[0].strip()
        params = entry.split("litellm_params:")[1]
        order = next(line.strip() for line in params.splitlines() if line.strip().startswith("order:"))
        orders_by_router.setdefault(router_id, []).append(order)
    for router_id, orders in orders_by_router.items():
        assert sorted(orders) == ["order: 1", "order: 2"], router_id


def test_litellm_zen_entries_have_openai_provider() -> None:
    for entry in _litellm_entries():
        params = entry.split("litellm_params:")[1]
        order = next(line.strip() for line in params.splitlines() if line.strip().startswith("order:"))
        if order == "order: 1":
            provider = next(
                line.strip() for line in params.splitlines() if line.strip().startswith("custom_llm_provider:")
            )
            assert provider == "custom_llm_provider: openai", entry


def test_litellm_router_settings() -> None:
    text = _LITELLM_CONFIG.read_text()
    assert "routing_strategy: simple-shuffle" in text
    assert "num_retries: 1" in text
    assert "timeout: 60" in text


def test_litellm_general_settings_master_key() -> None:
    assert "master_key: os.environ/LITELLM_MASTER_KEY" in _LITELLM_CONFIG.read_text()


def test_litellm_no_fallbacks() -> None:
    text = _LITELLM_CONFIG.read_text()
    assert "fallbacks" not in text
    assert "default_fallbacks" not in text


def test_compose_litellm_service() -> None:
    text = _COMPOSE.read_text()
    block = _service_block(text, "litellm")
    assert 'image: "ghcr.io/berriai/litellm:${LITELLM_VERSION}"' in block
    assert "ports:" not in block
    assert '- "host.docker.internal:host-gateway"' in block
    assert '"./litellm-config.yaml:/app/config.yaml:ro"' in block
    assert 'command: ["--config", "/app/config.yaml"]' in block
    assert 'restart: "unless-stopped"' in block
    assert _env_vars(block) == _LITELLM_ENV_VARS


def test_compose_openwebui_env() -> None:
    block = _service_block(_COMPOSE.read_text(), "open-webui")
    assert "WEBUI_AUTH=False" in block
    assert "DATABASE_ENABLE_SESSION_SHARING=true" in block
    for var in _OPENWEBUI_ENV_VARS:
        assert f"${{{var}}}" in block


def test_compose_searxng_unchanged() -> None:
    block = _service_block(_COMPOSE.read_text(), "searxng")
    assert "ghcr.io/searxng/searxng:2026.2.16-8e824017d" in block
    assert "127.0.0.1:13308:8080" in block


def _rendered_env_keys() -> set[str]:
    openwebui = _load_openwebui()
    keys = {
        "BRAVE_API_KEY",
        "OPENCODE_GO_API_KEY",
        "LITELLM_MASTER_KEY",
        "OPENWEBUI_ADMIN_API_KEY",
        "OLLAMA_API_KEY",
        "ZEN_API_BASE",
        "OLLAMA_API_BASE",
        "OLLAMA_MODEL",
        "LITELLM_VERSION",
    }
    for preset in openwebui["default_models"]:
        keys.add(f"ZEN_{preset.upper()}_MODEL")
    keys.update(openwebui["extra_env"].keys())
    return keys


def test_compose_env_vars_covered_by_rendered_env() -> None:
    compose_vars = set(re.findall(r"\$\{([A-Z_]+)\}", _COMPOSE.read_text()))
    assert compose_vars <= _rendered_env_keys()


def test_litellm_config_env_refs_covered_by_rendered_env() -> None:
    refs = set(re.findall(r"os\.environ/([A-Z_]+)", _LITELLM_CONFIG.read_text()))
    assert refs <= _rendered_env_keys()


def test_deploy_args_file_contract_keys() -> None:
    deploy_source = (_REPO_ROOT / "deploys" / "openwebui" / "deploy.py").read_text()
    for key in ('"base_url"', '"admin_api_key"', '"config_path"', '"models"', '"preset_id"', '"router_model_id"'):
        assert key in deploy_source
