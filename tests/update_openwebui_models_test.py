import importlib.util
import json
import os
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any, cast
from unittest.mock import patch

MODEL_IDS = [
    "chat",
    "chat_thinking",
    "web_research",
    "translate_de",
    "translate_en",
    "fix_grammar_en",
    "fix_grammar_de",
    "linux_cli",
]
ROUTER_MODEL_IDS = [
    "router-chat",
    "router-chat_thinking",
    "router-web_research",
    "router-translate_de",
    "router-translate_en",
    "router-fix_grammar_en",
    "router-fix_grammar_de",
    "router-linux_cli",
]
MODEL_FAMILIES = ["chat", "chat_thinking", "web_research", "translate", "grammar", "linux_cli"]
SECRET_PLACEHOLDERS = ["BRAVE_API_KEY", "ZEN_API_KEY", "OPENWEBUI_CALLER_KEY", "OPENWEBUI_ADMIN_API_KEY"]
EXTRA_ENV_KEYS = [
    "ENABLE_OPENAI_API",
    "OPENAI_API_BASE_URL",
    "OPENAI_API_KEYS",
    "DEFAULT_MODELS",
    "ENABLE_MODEL_FILTER",
    "MODEL_FILTER_LIST",
]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT_PATH = os.path.join(ROOT, "scripts", "update-openwebui-models.py")
DEPLOY_PATH = os.path.join(ROOT, "deploys", "openwebui", "deploy.py")
COMPOSE_PATH = os.path.join(ROOT, "deploys", "openwebui", "files", "docker-compose.yml")
AISIX_CONFIG_PATH = os.path.join(ROOT, "deploys", "openwebui", "files", "aisix-config.yaml")
RESOURCES_PATH = os.path.join(ROOT, "deploys", "openwebui", "files", "resources.yaml")
ALL_PATH = os.path.join(ROOT, "group_data", "all.py")
CI_PATH = os.path.join(ROOT, "group_data", "ci.py")


def load_module(name: str, path: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_all_module(name: str) -> ModuleType:
    with patch.dict(os.environ, {"CI": ""}):
        return load_module(name, ALL_PATH)


def load_reconciler() -> ModuleType:
    assert os.path.isfile(SCRIPT_PATH)
    return load_module("update_openwebui_models", SCRIPT_PATH)


def require_callable(module: ModuleType, name: str) -> Callable[..., Any]:
    function = cast(Callable[..., Any] | None, getattr(module, name, None))
    assert function is not None
    return function


def group_manifest(openwebui: dict[str, Any]) -> dict[str, Any]:
    return {
        "default_models": openwebui["default_models"],
        "model_map": openwebui["model_map"],
        "presets": openwebui["presets"],
    }


def secret_placeholder_keys_are_commented(path: str) -> None:
    lines = Path(path).read_text().splitlines()
    for key in SECRET_PLACEHOLDERS:
        marker = f'    "{key}": "",'
        index = lines.index(marker)
        assert lines[index - 1].strip().startswith("# Set in local.py"), (key, lines[index - 1])


def test_openwebui_group_data_contract() -> None:
    all_data = load_all_module("openwebui_all")
    openwebui = cast(dict[str, Any], all_data.openwebui)

    assert openwebui["enabled"] is True
    assert openwebui["router_backend"] == "aisix"
    assert openwebui["router_config_path"] == "aisix-config.yaml"
    assert openwebui["router_resources_path"] == "resources.yaml"
    assert openwebui["default_models"] == MODEL_IDS
    assert openwebui["model_map"] == dict(zip(MODEL_IDS, ROUTER_MODEL_IDS, strict=True))
    assert list(openwebui["model_map"]) == MODEL_IDS
    assert all(alias not in MODEL_IDS for alias in openwebui["model_map"].values())
    presets = cast(list[dict[str, Any]], openwebui["presets"])
    assert [preset["id"] for preset in presets] == MODEL_IDS
    assert [preset["name"] for preset in presets] == [
        "Chat",
        "Chat (Thinking)",
        "Web Research",
        "Translate to German",
        "Translate to English",
        "Fix English Grammar",
        "Fix German Grammar",
        "Linux CLI",
    ]
    assert [preset["web_search"] for preset in presets] == [False, False, True, False, False, False, False, False]
    assert all(preset["system"] for preset in presets)
    assert list(openwebui["extra_env"]) == EXTRA_ENV_KEYS
    assert openwebui["extra_env"]["OPENAI_API_KEYS"] == "${OPENWEBUI_CALLER_KEY}"
    assert openwebui["extra_env"]["OPENAI_API_BASE_URL"] == openwebui["openai_compatible_base_url"]
    assert openwebui["openai_compatible_base_url"] == "http://aisix:3000/v1"
    joined = ",".join(MODEL_IDS)
    assert openwebui["extra_env"]["DEFAULT_MODELS"] == joined
    assert openwebui["extra_env"]["MODEL_FILTER_LIST"] == joined
    for provider in ("zen", "ollama"):
        models = cast(dict[str, str], openwebui[provider]["models"])
        assert list(models) == MODEL_FAMILIES
        assert all(models.values())
    assert openwebui["zen"]["base_url"] == "https://opencode.ai/zen/go/v1"
    assert openwebui["ollama"]["base_url"] == "http://host.docker.internal:11434/v1"
    for key in SECRET_PLACEHOLDERS:
        assert openwebui[key] == ""
    assert openwebui["OLLAMA_API_KEY"] == "ollama"
    secret_placeholder_keys_are_commented(ALL_PATH)


def test_openwebui_ci_group_data_mirrors_non_secret_values() -> None:
    all_data = load_all_module("openwebui_all_mirror")
    ci_data = load_module("openwebui_ci", CI_PATH)
    all_openwebui = cast(dict[str, Any], all_data.openwebui)
    ci_openwebui = cast(dict[str, Any], ci_data.openwebui)

    assert ci_openwebui["enabled"] is False
    expected = {key: value for key, value in all_openwebui.items() if key not in SECRET_PLACEHOLDERS}
    expected["enabled"] = False
    assert ci_openwebui == expected
    assert json.dumps(ci_openwebui, sort_keys=True) == json.dumps(expected, sort_keys=True)
    for key in SECRET_PLACEHOLDERS:
        assert key not in ci_openwebui
