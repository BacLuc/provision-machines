import importlib.util
import os
from pathlib import Path
from typing import Any, cast

_GROUP_DATA = Path(__file__).resolve().parent.parent / "group_data" / "all.py"

_PRESET_IDS = [
    "chat",
    "chat_thinking",
    "web_research",
    "translate_de",
    "translate_en",
    "fix_grammar_en",
    "fix_grammar_de",
    "linux_cli",
]

_FAMILY_IDS = [
    "chat",
    "chat_thinking",
    "web_research",
    "translate",
    "fix_grammar",
    "linux_cli",
]

_SECRET_KEYS = {
    "BRAVE_API_KEY",
    "OPENCODE_GO_API_KEY",
    "OPENWEBUI_CALLER_KEY",
    "OPENWEBUI_ADMIN_API_KEY",
}


def _load_openwebui(ci: bool) -> dict[str, Any]:
    os.environ["CI"] = "1" if ci else ""
    spec = importlib.util.spec_from_file_location(f"group_data_all_{ci}", _GROUP_DATA)
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return cast(dict[str, Any], mod.openwebui)


def test_base_enabled_ci_disabled() -> None:
    assert _load_openwebui(False)["enabled"] is True
    assert _load_openwebui(True)["enabled"] is False


def test_ci_mirrors_base_non_secret_fields() -> None:
    base = _load_openwebui(False)
    ci = _load_openwebui(True)
    base_public = {k: v for k, v in base.items() if k not in _SECRET_KEYS and k != "enabled"}
    ci_public = {k: v for k, v in ci.items() if k not in _SECRET_KEYS and k != "enabled"}
    assert base_public == ci_public


def test_router_settings() -> None:
    openwebui = _load_openwebui(False)
    assert openwebui["router_backend"] == "aisix"
    assert openwebui["router_config_path"] == "aisix-resources.yaml"
    assert openwebui["openai_compatible_base_url"] == "http://aisix:3000/v1"


def test_default_models_order() -> None:
    assert _load_openwebui(False)["default_models"] == _PRESET_IDS


def test_model_map() -> None:
    openwebui = _load_openwebui(False)
    assert list(openwebui["model_map"].keys()) == _PRESET_IDS
    for preset, router_id in openwebui["model_map"].items():
        assert router_id.startswith("router-")
        assert router_id != preset


def test_extra_env() -> None:
    openwebui = _load_openwebui(False)
    assert openwebui["extra_env"] == {
        "ENABLE_OPENAI_API": "true",
        "OPENAI_API_BASE_URL": "${OPENAI_COMPATIBLE_BASE_URL}",
        "OPENAI_API_KEYS": "${OPENWEBUI_CALLER_KEY}",
        "DEFAULT_MODELS": ",".join(_PRESET_IDS),
        "ENABLE_MODEL_FILTER": "true",
        "MODEL_FILTER_LIST": ",".join(_PRESET_IDS),
    }


def test_zen() -> None:
    openwebui = _load_openwebui(False)
    assert openwebui["zen"]["base_url"] == "https://opencode.ai/zen/go/v1"
    assert set(openwebui["zen"]["models"].keys()) == set(_FAMILY_IDS)


def test_ollama() -> None:
    openwebui = _load_openwebui(False)
    assert openwebui["ollama"]["base_url"] == "http://host.docker.internal:11434/v1"
    assert openwebui["ollama"]["model"] == "qwen2.5:3b"


def test_secret_placeholders_empty() -> None:
    openwebui = _load_openwebui(False)
    for key in _SECRET_KEYS:
        assert openwebui[key] == ""
