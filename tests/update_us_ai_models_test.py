import importlib.util
import json
import os
import shutil
from pathlib import Path

_SCRIPT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "scripts",
    "update-us-ai-models.py",
)
_REAL_CONFIG = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "deploys",
    "development_tools",
    "ai_agent_devcontainer",
    "files",
    "opencode",
    "opencode.jsonc",
)
_spec = importlib.util.spec_from_file_location("update_us_ai_models", _SCRIPT)
assert _spec is not None
assert _spec.loader is not None
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)


def test_strip_jsonc_comments_removes_line_comments() -> None:
    text = '{\n  // hello\n  "x": 1\n}'
    assert mod.strip_jsonc_comments(text) == '{\n  \n  "x": 1\n}'


def test_strip_jsonc_comments_removes_block_comments() -> None:
    text = '{\n  /* block */\n  "x": 1\n}'
    assert mod.strip_jsonc_comments(text) == '{\n  \n  "x": 1\n}'


def test_strip_jsonc_comments_preserves_strings() -> None:
    text = '{"url": "http://example.com // not a comment"}'
    assert mod.strip_jsonc_comments(text) == text


def test_strip_jsonc_comments_preserves_escaped_quotes() -> None:
    text = '{"s": "say \\"hi\\" // still string"}'
    assert mod.strip_jsonc_comments(text) == text


def test_npm_name_unscoped() -> None:
    assert mod.npm_name("opencode-gemini-auth@1.4.9") == "opencode-gemini-auth"


def test_npm_name_scoped() -> None:
    assert mod.npm_name("@dietrichgebert/ponytail@4.8.4") == "@dietrichgebert/ponytail"


def test_npm_name_no_version() -> None:
    assert mod.npm_name("@scope/name") is None
    assert mod.npm_name("plain") is None


def _models_from_real_config() -> list[dict[str, str]]:
    with open(_REAL_CONFIG) as f:
        config = json.loads(mod.strip_jsonc_comments(f.read()))
    models = config["provider"][mod.PROVIDER_NAME]["models"]
    return [{"id": model_id, "name": model["name"]} for model_id, model in models.items()]


def _vshn_carrier_pins(path: str) -> set[str]:
    with open(path) as f:
        config = json.loads(mod.strip_jsonc_comments(f.read()))
    prefix = mod.PROVIDER_NAME + "/"
    return {
        str(agent["model"])
        for agent in config["agent"].values()
        if isinstance(agent, dict) and str(agent.get("model", "")).startswith(prefix)
    }


def test_update_config_preserves_comments_and_is_idempotent(tmp_path: Path) -> None:
    config_copy = tmp_path / "opencode.jsonc"
    shutil.copy(_REAL_CONFIG, config_copy)
    models = _models_from_real_config()
    mod.update_config(models, str(config_copy))
    first = config_copy.read_text()
    assert "// renovate: datasource=npm depName=@dietrichgebert/ponytail" in first
    assert "// renovate: datasource=npm depName=opencode-gemini-auth" in first
    mod.update_config(models, str(config_copy))
    assert config_copy.read_text() == first
    assert _vshn_carrier_pins(str(config_copy)) == {f"{mod.PROVIDER_NAME}/{model['id']}" for model in models}


def test_carrier_name_sanitizes_model_keys() -> None:
    assert mod.carrier_name("byusage.moonshot/kimi-k3") == "carrier-vshn-byusage-moonshot-kimi-k3"
    assert mod.carrier_name("-claude-haiku-v45") == "carrier-vshn-claude-haiku-v45"
    assert mod.carrier_name("subscription.qwen3.8-flash") == "carrier-vshn-subscription-qwen3-8-flash"


def test_update_config_syncs_carriers_on_added_and_removed_models(tmp_path: Path) -> None:
    config_copy = tmp_path / "opencode.jsonc"
    shutil.copy(_REAL_CONFIG, config_copy)
    models = _models_from_real_config()
    dropped = models[0]
    kept = [model for model in models if model is not dropped]
    added = {"id": "subscription.test-model-y", "name": "test-model-y"}
    mod.update_config(kept + [added], str(config_copy))
    text = config_copy.read_text()
    assert "// renovate: datasource=npm depName=@dietrichgebert/ponytail" in text
    prefix = mod.PROVIDER_NAME + "/"
    assert _vshn_carrier_pins(str(config_copy)) == {prefix + model["id"] for model in kept + [added]}
    config = json.loads(mod.strip_jsonc_comments(text))
    carrier = config["agent"]["carrier-vshn-subscription-test-model-y"]
    assert list(carrier) == ["mode", "hidden", "model", "description", "temperature", "steps", "permission", "prompt"]
    assert carrier["model"] == prefix + "subscription.test-model-y"
    assert carrier["description"] == "Carrier relay using vshn-us-ai subscription.test-model-y."
    assert "carrier-vshn-byusage-kimi-k3" in config["agent"]
    assert list(config["agent"])[-1] == "carrier-vshn-subscription-test-model-y"
