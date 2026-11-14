import importlib.util
import json
import os
from pathlib import Path

_SCRIPT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "scripts",
    "update-us-ai-models.py",
)
_CONFIG_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "deploys",
    "development_tools",
    "ai_agent_devcontainer",
    "files",
    "opencode",
)
_spec = importlib.util.spec_from_file_location("update_us_ai_models", _SCRIPT)
assert _spec is not None
assert _spec.loader is not None
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)


def test_normalize_jsonc_removes_line_comments() -> None:
    text = '{\n  // hello\n  "x": 1\n}'
    assert mod.normalize_jsonc(text) == '{\n  \n  "x": 1\n}'


def test_normalize_jsonc_removes_block_comments() -> None:
    text = '{\n  /* block */\n  "x": 1\n}'
    assert mod.normalize_jsonc(text) == '{\n  \n  "x": 1\n}'


def test_normalize_jsonc_preserves_strings() -> None:
    text = '{"url": "http://example.com // not a comment"}'
    assert mod.normalize_jsonc(text) == text


def test_normalize_jsonc_preserves_escaped_quotes() -> None:
    text = '{"s": "say \\"hi\\" // still string"}'
    assert mod.normalize_jsonc(text) == text


def test_npm_name_unscoped() -> None:
    assert mod.npm_name("opencode-gemini-auth@1.4.9") == "opencode-gemini-auth"


def test_npm_name_scoped() -> None:
    assert mod.npm_name("@dietrichgebert/ponytail@4.8.4") == "@dietrichgebert/ponytail"


def test_npm_name_no_version() -> None:
    assert mod.npm_name("@scope/name") is None
    assert mod.npm_name("plain") is None


def test_update_config_parses_the_repo_jsonc_files(tmp_path: Path) -> None:
    for name in ("opencode.jsonc", "untracked-config.example.jsonc"):
        with open(os.path.join(_CONFIG_DIR, name)) as f:
            target = tmp_path / name
            target.write_text(f.read())
        original_config = json.loads(mod.normalize_jsonc(target.read_text()))
        mod.update_config([{"id": "byusage.example/model", "name": "Model"}], config_path=target)
        with open(target) as f:
            config = json.loads(f.read())
        assert config["providers"]["vshn-us-ai"]["models"] == {
            "byusage.example/model": {"name": "Model (byusage)"},
        }
        assert (
            config["providers"]["vshn-us-ai"]["settings"]
            == original_config["providers"]["vshn-us-ai"]["settings"]
        )
        if name == "opencode.jsonc":
            for provider in ("cortecs2", "requesty2"):
                assert config["providers"][provider]["package"] == "aisdk:@ai-sdk/openai-compatible"
                assert config["providers"][provider]["settings"]["baseURL"]
                assert config["providers"][provider]["models"]
        assert "provider" not in config


def test_update_config_preserves_legacy_v1_config(tmp_path: Path) -> None:
    target = tmp_path / "config.json"
    target.write_text(
        json.dumps(
            {
                "theme": {"name": "opencode"},
                "provider": {
                    "other": {"npm": "@ai-sdk/other", "name": "Other"},
                    "vshn-us-ai": {
                        "npm": "@ai-sdk/openai-compatible",
                        "name": "VSHN US AI",
                        "options": {
                            "baseURL": "https://legacy.example/v1",
                            "apiKey": "{env:LEGACY_KEY}",
                        },
                        "models": {"old/model": {"name": "Old"}},
                    },
                },
            }
        )
    )

    mod.update_config([{"id": "byusage.example/model", "name": "Model"}], config_path=target)

    config = json.loads(target.read_text())
    provider = config["provider"]["vshn-us-ai"]
    assert "providers" not in config
    assert provider["options"] == {
        "baseURL": "https://legacy.example/v1",
        "apiKey": "{env:LEGACY_KEY}",
    }
    assert provider["npm"] == "@ai-sdk/openai-compatible"
    assert provider["models"] == {"byusage.example/model": {"name": "Model (byusage)"}}
    assert "package" not in provider
    assert config["provider"]["other"] == {"npm": "@ai-sdk/other", "name": "Other"}
    assert config["theme"] == {"name": "opencode"}


def test_update_config_updates_v2_in_place_without_copying_legacy(tmp_path: Path) -> None:
    legacy_entry = {
        "npm": "@ai-sdk/openai-compatible",
        "name": "Legacy",
        "options": {"baseURL": "https://legacy.example/v1"},
        "models": {"legacy/model": {"name": "Legacy"}},
    }
    target = tmp_path / "config.json"
    target.write_text(
        json.dumps(
            {
                "providers": {
                    "other-v2": {"package": "aisdk:other", "name": "Other V2"},
                    "vshn-us-ai": {
                        "package": "aisdk:old",
                        "name": "Old",
                        "settings": {"baseURL": "https://v2.example/v1"},
                        "models": {"old/model": {"name": "Old"}},
                    },
                },
                "provider": {
                    "other-v1": {"npm": "@ai-sdk/other", "name": "Other V1"},
                    "vshn-us-ai": legacy_entry,
                },
            }
        )
    )

    mod.update_config([{"id": "byusage.example/model", "name": "Model"}], config_path=target)

    config = json.loads(target.read_text())
    v2 = config["providers"]["vshn-us-ai"]
    assert v2["settings"] == {"baseURL": "https://v2.example/v1"}
    assert v2["models"] == {"byusage.example/model": {"name": "Model (byusage)"}}
    assert v2["package"] == "aisdk:@ai-sdk/openai-compatible"
    assert "npm" not in v2
    assert config["provider"]["vshn-us-ai"] == legacy_entry
    assert "other-v1" not in config["providers"]
    assert config["providers"]["other-v2"] == {"package": "aisdk:other", "name": "Other V2"}


def test_update_config_does_not_duplicate_legacy_provider_into_v2(tmp_path: Path) -> None:
    target = tmp_path / "config.json"
    target.write_text(
        json.dumps(
            {
                "providers": {"other-v2": {"package": "aisdk:other", "name": "Other V2"}},
                "provider": {
                    "vshn-us-ai": {
                        "npm": "@ai-sdk/openai-compatible",
                        "name": "VSHN US AI",
                        "options": {"baseURL": "https://legacy.example/v1"},
                        "models": {"old/model": {"name": "Old"}},
                    }
                },
            }
        )
    )

    mod.update_config([{"id": "byusage.example/model", "name": "Model"}], config_path=target)

    config = json.loads(target.read_text())
    legacy = config["provider"]["vshn-us-ai"]
    assert "vshn-us-ai" not in config["providers"]
    assert legacy["options"] == {"baseURL": "https://legacy.example/v1"}
    assert legacy["npm"] == "@ai-sdk/openai-compatible"
    assert legacy["models"] == {"byusage.example/model": {"name": "Model (byusage)"}}
    assert config["providers"]["other-v2"] == {"package": "aisdk:other", "name": "Other V2"}


def test_update_config_creates_v2_provider_when_no_container_exists(tmp_path: Path) -> None:
    target = tmp_path / "config.json"
    target.write_text(json.dumps({"theme": {"name": "opencode"}}))

    mod.update_config([{"id": "byusage.example/model", "name": "Model"}], config_path=target)

    config = json.loads(target.read_text())
    assert config["providers"]["vshn-us-ai"]["package"] == "aisdk:@ai-sdk/openai-compatible"
    assert config["providers"]["vshn-us-ai"]["name"] == "VSHN US AI"
    assert config["providers"]["vshn-us-ai"]["models"] == {
        "byusage.example/model": {"name": "Model (byusage)"}
    }
    assert "provider" not in config
    assert config["theme"] == {"name": "opencode"}
