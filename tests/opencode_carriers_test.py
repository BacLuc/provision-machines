import importlib.util
import json
import os
import re
from pathlib import Path
from typing import Any

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_OPENCODE_DIR = os.path.join(
    _REPO,
    "deploys",
    "development_tools",
    "ai_agent_devcontainer",
    "files",
    "opencode",
)
_CONFIG_PATH = os.path.join(_OPENCODE_DIR, "opencode.jsonc")
_COORDINATOR_PATH = os.path.join(_OPENCODE_DIR, "agents", "coordinator.md")
_SCRIPT = os.path.join(_REPO, "scripts", "update-us-ai-models.py")

_spec = importlib.util.spec_from_file_location("update_us_ai_models", _SCRIPT)
assert _spec is not None
assert _spec.loader is not None
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)

ZEN_FREE_IDS = [
    "deepseek-v4-flash-free",
    "laguna-s-2.1-free",
    "ling-3.0-flash-fin-free",
    "mimo-v2.5-free",
    "muse-spark-1.2-contributor-free",
    "muse-spark-1.3-contributor-free",
    "nemotron-3-ultra-free",
    "nemotron-3.5-lightning-free",
]


def _raw_text() -> str:
    return Path(_CONFIG_PATH).read_text()


def _parsed() -> dict[str, Any]:
    parsed: dict[str, Any] = json.loads(mod.strip_jsonc_comments(_raw_text()))
    return parsed


def _carriers(parsed: dict[str, Any]) -> dict[str, Any]:
    return {name: agent for name, agent in parsed["agent"].items() if name.startswith("carrier-")}


def _provider_pins(parsed: dict[str, Any]) -> set[str]:
    return {
        f"{provider_key}/{model_key}"
        for provider_key, provider in parsed["provider"].items()
        for model_key in provider.get("models", {})
    }


def test_config_parses_after_stripping_line_comments() -> None:
    parsed = _parsed()
    assert "agent" in parsed
    assert "provider" in parsed


def test_every_provider_model_has_exactly_one_carrier() -> None:
    parsed = _parsed()
    pins = [str(agent.get("model", "")) for agent in _carriers(parsed).values()]
    for pin in sorted(_provider_pins(parsed)):
        assert pins.count(pin) == 1, pin


def test_every_carrier_pins_a_known_model() -> None:
    parsed = _parsed()
    known = _provider_pins(parsed) | {"openai/gpt-5.6-terra"}
    known |= {f"opencode/{model_id}" for model_id in ZEN_FREE_IDS}
    for name, agent in _carriers(parsed).items():
        assert str(agent.get("model", "")) in known, name


def test_coordinator_roster_lists_carriers_in_file_order() -> None:
    coordinator = Path(_COORDINATOR_PATH).read_text()
    section = coordinator.split(
        "### Every normal work-agent dispatch: model discovery and carrier routing",
        1,
    )[1]
    match = re.search(r"```\n(.*?)```", section, re.S)
    assert match is not None
    roster = [line.strip() for line in match.group(1).splitlines() if line.strip()]
    assert roster == list(_carriers(_parsed()))


def test_renovate_ponytail_directive_survives_in_raw_config() -> None:
    assert "renovate: datasource=npm depName=@dietrichgebert/ponytail" in _raw_text()
