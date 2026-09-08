import importlib.util
import json
import os
from typing import Any

_SCRIPT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "scripts",
    "update-us-ai-models.py",
)
_spec = importlib.util.spec_from_file_location("update_us_ai_models", _SCRIPT)
assert _spec is not None
assert _spec.loader is not None
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)

_CONFIG = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "deploys",
    "development_tools",
    "ai_agent_devcontainer",
    "files",
    "opencode",
    "opencode.jsonc",
)
_UNTRACKED_CONFIG = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "deploys",
    "development_tools",
    "ai_agent_devcontainer",
    "files",
    "opencode",
    "untracked-config.example.jsonc",
)


def _load_config(path: str) -> Any:
    with open(path) as f:
        return json.loads(mod.strip_jsonc_comments(f.read()))


def test_kiro_plugin_is_configured() -> None:
    config = _load_config(_CONFIG)
    plugins = config["plugin"]
    assert any(
        isinstance(p, str) and "opencode-kiro-auth" in p
        for p in plugins
    )


def test_kiro_provider_requires_no_api_key() -> None:
    config = _load_config(_CONFIG)
    kiro = config["provider"].get("kiro")
    assert kiro is None


def test_kiro_has_no_api_key_in_untracked_config_example() -> None:
    config = _load_config(_UNTRACKED_CONFIG)
    assert "kiro" not in config["provider"]
