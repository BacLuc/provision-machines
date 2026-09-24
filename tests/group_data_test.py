import importlib.util
import os
from pathlib import Path
from typing import Any, cast

_GROUP_DATA = Path(__file__).resolve().parent.parent / "group_data" / "all.py"
_CI_DATA = Path(__file__).resolve().parent.parent / "group_data" / "ci.py"

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

_SECRET_KEYS = {
    "BRAVE_API_KEY",
    "OPENCODE_GO_API_KEY",
    "LITELLM_MASTER_KEY",
    "OPENWEBUI_ADMIN_API_KEY",
}


def _load(path: Path, name: str) -> dict[str, Any]:
    # all.py applies ci.py overrides when CI is set; the tests load the
    # files directly, so clear it to get the base/ci definitions as-is.
    os.environ["CI"] = ""
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return cast(dict[str, Any], mod.openwebui)


def test_base_enabled_ci_disabled() -> None:
    assert _load(_GROUP_DATA, "group_data_all")["enabled"] is True
    assert _load(_CI_DATA, "group_data_ci")["enabled"] is False


def test_ci_only_overrides_enabled_and_secrets() -> None:
    # pyinfra deep-merges group data, so ci.py only needs to override what
    # differs from all.py: the enabled flag and the secret placeholders.
    ci = _load(_CI_DATA, "group_data_ci")
    assert set(ci.keys()) == {"enabled"} | _SECRET_KEYS
    for key in _SECRET_KEYS:
        assert ci[key] == ""


def test_router_settings() -> None:
    openwebui = _load(_GROUP_DATA, "group_data_all")
    assert openwebui["router_backend"] == "litellm"
    assert openwebui["router_config_path"] == "litellm-config.yaml"
    assert openwebui["openai_compatible_base_url"] == "http://litellm:4000/v1"


def test_default_models_order() -> None:
    assert _load(_GROUP_DATA, "group_data_all")["default_models"] == _PRESET_IDS


def test_model_map() -> None:
    openwebui = _load(_GROUP_DATA, "group_data_all")
    assert list(openwebui["model_map"].keys()) == _PRESET_IDS
    for preset, router_id in openwebui["model_map"].items():
        assert router_id.startswith("router-")
        assert router_id != preset


def test_extra_env() -> None:
    openwebui = _load(_GROUP_DATA, "group_data_all")
    assert openwebui["extra_env"] == {
        "ENABLE_OPENAI_API": "true",
        "OPENAI_API_BASE_URL": "http://litellm:4000/v1",
        "OPENAI_API_KEYS": "${LITELLM_MASTER_KEY}",
        "DEFAULT_MODELS": ",".join(_PRESET_IDS),
    }


def test_zen() -> None:
    openwebui = _load(_GROUP_DATA, "group_data_all")
    assert openwebui["zen"]["base_url"] == "https://opencode.ai/zen/go/v1"
    assert set(openwebui["zen"]["models"].keys()) == set(_PRESET_IDS)


def test_ollama() -> None:
    openwebui = _load(_GROUP_DATA, "group_data_all")
    assert openwebui["ollama"]["base_url"] == "http://host.docker.internal:11434"
    assert openwebui["ollama"]["model"] == "qwen2.5:3b"


def test_secret_placeholders_empty() -> None:
    openwebui = _load(_GROUP_DATA, "group_data_all")
    for key in _SECRET_KEYS:
        assert openwebui[key] == ""
