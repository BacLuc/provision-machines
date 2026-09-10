import importlib.util
import json
import os
from typing import cast

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

_OPENCODE_CONFIG = os.path.join(
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


def _load_jsonc(path: str) -> dict[str, object]:
    with open(path, encoding="utf-8") as f:
        return cast(dict[str, object], json.loads(mod.strip_jsonc_comments(f.read())))


def test_openrouter_provider_in_opencode_config() -> None:
    config = _load_jsonc(_OPENCODE_CONFIG)
    providers = config["provider"]
    assert isinstance(providers, dict)
    openrouter = providers["openrouter"]
    assert isinstance(openrouter, dict)
    options = openrouter["options"]
    assert isinstance(options, dict)
    assert options["baseURL"] == "https://openrouter.ai/api/v1"
    models = openrouter["models"]
    assert isinstance(models, dict)
    assert len(models) > 0


def test_openrouter_provider_in_untracked_config() -> None:
    config = _load_jsonc(_UNTRACKED_CONFIG)
    providers = config["provider"]
    assert isinstance(providers, dict)
    openrouter = providers["openrouter"]
    assert isinstance(openrouter, dict)
    options = openrouter["options"]
    assert isinstance(options, dict)
    assert options["apiKey"] == "apikey"
