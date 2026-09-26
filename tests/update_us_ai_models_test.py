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
        mod.update_config([{"id": "byusage.example/model", "name": "Model"}], config_path=target)
        with open(target) as f:
            config = json.loads(f.read())
        assert config["provider"]["vshn-us-ai"]["models"] == {
            "byusage.example/model": {"name": "Model (byusage)"},
        }
