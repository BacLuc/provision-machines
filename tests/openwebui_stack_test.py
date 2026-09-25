import importlib.util
import os
import re
from pathlib import Path
from typing import Any, cast

_REPO_ROOT = Path(__file__).resolve().parent.parent
_AISIX_CONFIG = _REPO_ROOT / "deploys" / "openwebui" / "files" / "aisix-config.yaml"
_AISIX_RESOURCES = _REPO_ROOT / "deploys" / "openwebui" / "files" / "aisix-resources.yaml"
_COMPOSE = _REPO_ROOT / "deploys" / "openwebui" / "files" / "docker-compose.yml"

_AISIX_ENV_VARS = [
    "OPENCODE_GO_API_KEY",
    "OLLAMA_API_KEY",
    "OPENWEBUI_CALLER_KEY",
    "OLLAMA_API_BASE",
    "ZEN_API_BASE",
    "ZEN_MODEL_CHAT",
    "ZEN_MODEL_CHAT_THINKING",
    "ZEN_MODEL_WEB_RESEARCH",
    "ZEN_MODEL_TRANSLATE",
    "ZEN_MODEL_FIX_GRAMMAR",
    "ZEN_MODEL_LINUX_CLI",
    "OLLAMA_MODEL",
]

_ZEN_MODEL_ENV = {
    "chat": "ZEN_MODEL_CHAT",
    "chat_thinking": "ZEN_MODEL_CHAT_THINKING",
    "web_research": "ZEN_MODEL_WEB_RESEARCH",
    "translate": "ZEN_MODEL_TRANSLATE",
    "fix_grammar": "ZEN_MODEL_FIX_GRAMMAR",
    "linux_cli": "ZEN_MODEL_LINUX_CLI",
}

_OPENWEBUI_ENV_VARS = [
    "ENABLE_OPENAI_API",
    "OPENAI_API_BASE_URL",
    "OPENAI_API_KEYS",
    "DEFAULT_MODELS",
    "ENABLE_MODEL_FILTER",
    "MODEL_FILTER_LIST",
]


def _load_openwebui() -> dict[str, Any]:
    os.environ["CI"] = ""
    spec = importlib.util.spec_from_file_location("group_data_all_stack", _REPO_ROOT / "group_data" / "all.py")
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return cast(dict[str, Any], mod.openwebui)


def _model_entries() -> list[str]:
    text = _AISIX_RESOURCES.read_text()
    models_section = text.split("\nmodels:\n", 1)[1].split("\napi_keys:", 1)[0]
    return re.split(r"\n  - display_name: ", "\n" + models_section)[1:]


def _service_block(text: str, name: str) -> str:
    match = re.search(rf"^  {name}:$.*?(?=^  [a-z-]+:$|^volumes:)", text, re.MULTILINE | re.DOTALL)
    assert match is not None, f"service {name} not found"
    return match.group(0)


def _env_vars(block: str) -> list[str]:
    return re.findall(r'^      - "([A-Z_]+)=', block, re.MULTILINE)


def test_aisix_config_is_bootstrap_only() -> None:
    text = _AISIX_CONFIG.read_text()
    assert "resources_file: /etc/aisix/resources.yaml" in text
    assert "0.0.0.0:3000" in text


def test_aisix_resources_shape() -> None:
    text = _AISIX_RESOURCES.read_text()
    assert '_format_version: "1"' in text
    provider_section = text.split("provider_keys:", 1)[1].split("\nmodels:", 1)[0]
    assert len(re.findall(r"display_name:", provider_section)) == 2
    entries = _model_entries()
    assert len(entries) == 20
    direct = [entry for entry in entries if "\n    routing:" not in entry]
    aliases = [entry for entry in entries if "\n    routing:" in entry]
    assert len(direct) == 12
    assert len(aliases) == 8
    caller_section = text.split("\napi_keys:", 1)[1]
    assert len(re.findall(r"display_name:", caller_section)) == 1


def test_aisix_router_aliases_match_model_map() -> None:
    aliases = {entry.splitlines()[0].strip() for entry in _model_entries() if "\n    routing:" in entry}
    assert aliases == set(_load_openwebui()["model_map"].values())


def test_aisix_aliases_failover_zen_first() -> None:
    for entry in _model_entries():
        if "\n    routing:" not in entry:
            continue
        alias = entry.splitlines()[0].strip()
        assert "strategy: failover" in entry, alias
        assert "max_fallbacks: 1" in entry, alias
        assert "retry_on_429: true" in entry, alias
        targets = re.findall(r"- model: (\S+)\n\s+priority: (-?\d+)", entry)
        assert len(targets) == 2, alias
        assert targets[0][1] == "100" and targets[0][0].startswith("zen-"), alias
        assert targets[1][1] == "-1" and targets[1][0].startswith("ollama-"), alias


def test_aisix_api_bases_are_openai_compatible() -> None:
    openwebui = _load_openwebui()
    bases = {
        "ZEN_API_BASE": openwebui["zen"]["base_url"],
        "OLLAMA_API_BASE": openwebui["ollama"]["base_url"],
    }
    refs = set()
    for line in _AISIX_RESOURCES.read_text().splitlines():
        stripped = line.strip()
        if stripped.startswith("api_base:"):
            match = re.fullmatch(r"api_base: \$\{([A-Z_]+)\}", stripped)
            assert match is not None, stripped
            refs.add(match.group(1))
    assert refs == set(bases)
    for var, base in bases.items():
        assert base.endswith("/v1"), (var, base)


def test_aisix_resources_use_env_only() -> None:
    text = _AISIX_RESOURCES.read_text()
    for key in ("api_base:", "api_key:", "model_name:"):
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith(key):
                assert "${" in stripped, stripped


def test_aisix_caller_key_allows_all_aliases() -> None:
    text = _AISIX_RESOURCES.read_text()
    assert "key_env: OPENWEBUI_CALLER_KEY" in text
    allowed = re.search(r"allowed_models:\n((?:      - \S+\n)+)", text)
    assert allowed is not None
    models = re.findall(r"- (\S+)", allowed.group(1))
    assert set(models) == set(_load_openwebui()["model_map"].values())


def test_compose_aisix_service() -> None:
    text = _COMPOSE.read_text()
    block = _service_block(text, "aisix")
    assert 'image: "ghcr.io/api7/aisix:${AISIX_VERSION}"' in block
    assert "ports:" not in block
    assert '"3000"' in block
    assert '- "host.docker.internal:host-gateway"' in block
    assert '"./aisix-config.yaml:/etc/aisix/config.yaml:ro"' in block
    assert '"./aisix-resources.yaml:/etc/aisix/resources.yaml:ro"' in block
    assert 'restart: "unless-stopped"' in block
    assert _env_vars(block) == _AISIX_ENV_VARS


def test_compose_openwebui_env() -> None:
    block = _service_block(_COMPOSE.read_text(), "open-webui")
    assert "WEBUI_AUTH=False" in block
    assert "DATABASE_ENABLE_SESSION_SHARING=true" in block
    assert "http://aisix:3000/v1" not in block
    for var in _OPENWEBUI_ENV_VARS:
        assert f"${{{var}}}" in block


def test_compose_no_router_port_published() -> None:
    text = _COMPOSE.read_text()
    assert "4000" not in text
    assert "litellm" not in text


def test_compose_searxng_unchanged() -> None:
    block = _service_block(_COMPOSE.read_text(), "searxng")
    assert "ghcr.io/searxng/searxng:2026.2.16-8e824017d" in block
    assert "127.0.0.1:13308:8080" in block


def _rendered_env_keys() -> set[str]:
    openwebui = _load_openwebui()
    keys = {
        "BRAVE_API_KEY",
        "OPENCODE_GO_API_KEY",
        "OPENWEBUI_CALLER_KEY",
        "OPENWEBUI_ADMIN_API_KEY",
        "OLLAMA_API_KEY",
        "ZEN_API_BASE",
        "OLLAMA_API_BASE",
        "OLLAMA_MODEL",
        "AISIX_VERSION",
    }
    keys.update(_ZEN_MODEL_ENV.values())
    keys.update(openwebui["extra_env"].keys())
    return keys


def test_compose_env_vars_covered_by_rendered_env() -> None:
    compose_vars = set(re.findall(r"\$\{([A-Z_]+)\}", _COMPOSE.read_text()))
    assert compose_vars <= _rendered_env_keys()


def test_aisix_resources_env_refs_covered_by_rendered_env() -> None:
    refs = set(re.findall(r"\$\{([A-Z_]+)\}", _AISIX_RESOURCES.read_text()))
    assert refs <= _rendered_env_keys()


def test_deploy_args_file_contract_keys() -> None:
    deploy_source = (_REPO_ROOT / "deploys" / "openwebui" / "deploy.py").read_text()
    for key in ('"base_url"', '"admin_api_key"', '"config_path"', '"models"', '"preset_id"', '"router_model_id"'):
        assert key in deploy_source


def test_deploy_validates_and_reloads_aisix() -> None:
    deploy_source = (_REPO_ROOT / "deploys" / "openwebui" / "deploy.py").read_text()
    assert "validate --resources" in deploy_source
    assert "docker kill --signal=HUP aisix" in deploy_source
    assert "aisix-resources.yaml" in deploy_source
    assert "litellm" not in deploy_source.lower()
