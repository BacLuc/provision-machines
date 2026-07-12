import importlib.util
import os

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


def test_inject_plugin_comments_inserts_renovate_lines() -> None:
    text = '{\n  "plugin": [\n    "foo@1.0",\n    "bar@2.0"\n  ]\n}'
    result = mod.inject_plugin_comments(text, ["foo@1.0", "bar@2.0"])
    assert "// renovate: datasource=npm depName=foo" in result
    assert "// renovate: datasource=npm depName=bar" in result
    assert result.count("// renovate:") == 2
    assert '"foo@1.0"' in result
    assert '"bar@2.0"' in result


def test_inject_plugin_comments_skips_no_version() -> None:
    text = '{\n  "plugin": [\n    "noversion",\n    "bar@2.0"\n  ]\n}'
    result = mod.inject_plugin_comments(text, ["noversion", "bar@2.0"])
    assert result.count("// renovate:") == 1
    assert "// renovate: datasource=npm depName=bar" in result


def test_round_trip_preserves_plugins_with_comments() -> None:
    import json

    config = {
        "$schema": "https://opencode.ai/config.json",
        "plugin": ["opencode-gemini-auth@1.4.9", "opencode-auto-resume@1.0.18"],
        "provider": {"vshn-us-ai": {"name": "VSHN US AI"}},
    }
    text = json.dumps(config, indent=2)
    text = mod.inject_plugin_comments(text, config["plugin"])
    reparsed = json.loads(mod.strip_jsonc_comments(text))
    assert reparsed["plugin"] == config["plugin"]
    assert reparsed["provider"] == config["provider"]
