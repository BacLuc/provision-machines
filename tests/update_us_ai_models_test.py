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


def test_tracked_configs_use_consistent_v1_format() -> None:
    for name in ("opencode.jsonc", "untracked-config.example.jsonc"):
        config = json.loads(mod.normalize_jsonc((Path(_CONFIG_DIR) / name).read_text()))
        assert "provider" in config
        assert "providers" not in config
        pending = [config]
        while pending:
            node = pending.pop()
            if isinstance(node, dict):
                assert "package" not in node
                assert "settings" not in node
                pending.extend(node.values())
            elif isinstance(node, list):
                pending.extend(node)


def test_update_config_parses_the_repo_jsonc_files(tmp_path: Path) -> None:
    for name in ("opencode.jsonc", "untracked-config.example.jsonc"):
        with open(os.path.join(_CONFIG_DIR, name)) as f:
            target = tmp_path / name
            target.write_text(f.read())
        original_config = json.loads(mod.normalize_jsonc(target.read_text()))
        mod.update_config([{"id": "byusage.example/model", "name": "Model"}], config_path=target)
        config = json.loads(mod.normalize_jsonc(target.read_text()))
        provider = config["provider"]["vshn-us-ai"]
        assert provider["models"] == {"byusage.example/model": {"name": "Model (byusage)"}}
        assert provider["options"] == original_config["provider"]["vshn-us-ai"]["options"]
        assert provider["npm"] == "@ai-sdk/openai-compatible"
        assert provider["name"] == "VSHN US AI"
        assert "providers" not in config
        if name == "opencode.jsonc":
            for provider_name in ("cortecs2", "requesty2"):
                entry = config["provider"][provider_name]
                assert entry["options"]["baseURL"]
                assert entry["models"]
                assert "settings" not in entry
                assert "package" not in entry
            assert config["provider"]["openrouter"]["npm"] == "@ai-sdk/openai-compatible"


def test_update_config_preserves_renovate_directives(tmp_path: Path) -> None:
    with open(os.path.join(_CONFIG_DIR, "opencode.jsonc")) as f:
        original = f.read()
    target = tmp_path / "opencode.jsonc"
    target.write_text(original)

    mod.update_config([{"id": "byusage.example/model", "name": "Model"}], config_path=target)

    written = target.read_text()
    original_directives = [line for line in original.splitlines() if "// renovate:" in line]
    written_directives = [line for line in written.splitlines() if "// renovate:" in line]
    assert len(original_directives) == 6
    assert written_directives == original_directives


def test_repo_configs_remain_valid_v1_after_update(tmp_path: Path) -> None:
    for name in ("opencode.jsonc", "untracked-config.example.jsonc"):
        with open(os.path.join(_CONFIG_DIR, name)) as f:
            target = tmp_path / name
            target.write_text(f.read())
        mod.update_config([{"id": "byusage.example/model", "name": "Model"}], config_path=target)
        config = json.loads(mod.normalize_jsonc(target.read_text()))
        assert "provider" in config
        assert "providers" not in config
        provider = config["provider"]["vshn-us-ai"]
        assert provider["options"]
        assert provider["models"]
        for entry in config["provider"].values():
            assert "package" not in entry
            assert "settings" not in entry


def test_update_config_updates_existing_vshn_provider_in_place(tmp_path: Path) -> None:
    target = tmp_path / "config.json"
    target.write_text(
        json.dumps(
            {
                "provider": {
                    "other": {"npm": "@ai-sdk/other", "name": "Other"},
                    "vshn-us-ai": {
                        "npm": "aisdk:old",
                        "name": "Old",
                        "options": {"baseURL": "https://v1.example/v1"},
                        "models": {"old/model": {"name": "Old"}},
                    },
                },
            }
        )
    )

    mod.update_config([{"id": "byusage.example/model", "name": "Model"}], config_path=target)

    config = json.loads(target.read_text())
    provider = config["provider"]["vshn-us-ai"]
    assert provider["npm"] == "@ai-sdk/openai-compatible"
    assert provider["name"] == "VSHN US AI"
    assert provider["models"] == {"byusage.example/model": {"name": "Model (byusage)"}}
    assert provider["options"] == {"baseURL": "https://v1.example/v1"}
    assert config["provider"]["other"] == {"npm": "@ai-sdk/other", "name": "Other"}
    assert "providers" not in config


def test_update_config_creates_vshn_provider_in_existing_container(tmp_path: Path) -> None:
    target = tmp_path / "config.json"
    target.write_text(
        json.dumps(
            {
                "theme": {"name": "opencode"},
                "provider": {"other": {"npm": "@ai-sdk/other", "name": "Other"}},
            }
        )
    )

    mod.update_config([{"id": "byusage.example/model", "name": "Model"}], config_path=target)

    config = json.loads(target.read_text())
    provider = config["provider"]["vshn-us-ai"]
    assert provider["npm"] == "@ai-sdk/openai-compatible"
    assert provider["name"] == "VSHN US AI"
    assert provider["models"] == {"byusage.example/model": {"name": "Model (byusage)"}}
    assert config["provider"]["other"] == {"npm": "@ai-sdk/other", "name": "Other"}
    assert config["theme"] == {"name": "opencode"}
    assert "providers" not in config


def test_update_config_creates_v1_provider_when_no_container_exists(tmp_path: Path) -> None:
    target = tmp_path / "config.json"
    target.write_text(json.dumps({"theme": {"name": "opencode"}}))

    mod.update_config([{"id": "byusage.example/model", "name": "Model"}], config_path=target)

    config = json.loads(target.read_text())
    provider = config["provider"]["vshn-us-ai"]
    assert provider["npm"] == "@ai-sdk/openai-compatible"
    assert provider["name"] == "VSHN US AI"
    assert provider["models"] == {"byusage.example/model": {"name": "Model (byusage)"}}
    assert "providers" not in config
    assert config["theme"] == {"name": "opencode"}


def test_update_config_accepts_trailing_root_comma_when_creating_provider(tmp_path: Path) -> None:
    target = tmp_path / "config.jsonc"
    target.write_text('{"theme": {"name": "opencode"},}')

    mod.update_config([{"id": "byusage.example/model", "name": "Model"}], config_path=target)

    config = json.loads(mod.normalize_jsonc(target.read_text()))
    assert config["provider"]["vshn-us-ai"]["models"] == {
        "byusage.example/model": {"name": "Model (byusage)"}
    }
    assert config["theme"] == {"name": "opencode"}


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
    assert "settings" not in provider
    assert config["provider"]["other"] == {"npm": "@ai-sdk/other", "name": "Other"}
    assert config["theme"] == {"name": "opencode"}
