import importlib.util
import json
import os
import re

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_JSONC_PATH = os.path.join(
    _ROOT,
    "deploys",
    "development_tools",
    "ai_agent_devcontainer",
    "files",
    "opencode",
    "opencode.jsonc",
)
_COMPOSE_PATH = os.path.join(_ROOT, "deploys", "development_tools", "ai_agent_devcontainer", "files", "compose.yml")
_RENOVATE_PATH = os.path.join(_ROOT, "renovate.json")
_SCRIPT = os.path.join(_ROOT, "scripts", "update-us-ai-models.py")
_spec = importlib.util.spec_from_file_location("update_us_ai_models", _SCRIPT)
assert _spec is not None
assert _spec.loader is not None
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)

with open(_JSONC_PATH) as _f:
    _JSONC_TEXT = _f.read()
_JSONC = json.loads(mod.strip_jsonc_comments(_JSONC_TEXT))
with open(_COMPOSE_PATH) as _f:
    _COMPOSE_TEXT = _f.read()
with open(_RENOVATE_PATH) as _f:
    _RENOVATE = json.loads(_f.read())
_BRAVE_SERVER = "@brave/brave-search-mcp-server@2.1.4"


def test_brave_search_mcp_server_config() -> None:
    server = _JSONC["mcp"]["brave-search"]
    assert server["type"] == "local"
    assert server["command"] == ["npx", "-y", _BRAVE_SERVER, "--transport", "stdio"]
    assert server["enabled"] is True
    assert server["environment"] == {"BRAVE_API_KEY": "{env:BRAVE_API_KEY}"}
    assert re.search(r'"BRAVE_API_KEY"\s*:\s*"(?!\{env:BRAVE_API_KEY\})', _JSONC_TEXT) is None


def test_renovate_extracts_brave_search_mcp_server() -> None:
    manager = next(m for m in _RENOVATE["customManagers"] if r"\.jsonc$" in m["managerFilePatterns"][0])
    pattern = re.compile(manager["matchStrings"][0].replace("(?<", "(?P<"))
    matches = {m.group("depName"): m for m in pattern.finditer(_JSONC_TEXT)}
    match = matches["@brave/brave-search-mcp-server"]
    assert match.group("datasource") == "npm"
    assert match.group("currentValue") == "2.1.4"


def test_compose_passes_brave_api_key_to_devcontainer() -> None:
    assert "- BRAVE_API_KEY" in _COMPOSE_TEXT
