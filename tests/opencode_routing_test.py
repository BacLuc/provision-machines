import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, cast


ROOT = Path(__file__).parents[1]
OPENCODE = ROOT / "deploys/development_tools/ai_agent_devcontainer/files/opencode"
SCRIPT = ROOT / "scripts/update-us-ai-models.py"


def load_config() -> dict[str, Any]:
    spec = importlib.util.spec_from_file_location("update_us_ai_models", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return cast(dict[str, Any], json.loads(module.strip_jsonc_comments((OPENCODE / "opencode.jsonc").read_text())))


def test_config_parses_and_loads_markdown_discovery() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import importlib.util,json,sys; spec=importlib.util.spec_from_file_location('models',sys.argv[1]); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); json.loads(mod.strip_jsonc_comments(open(sys.argv[2]).read()))",
            str(SCRIPT),
            str(OPENCODE / "opencode.jsonc"),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    config = load_config()
    assert config["extends"] == ["./untracked-config.jsonc"]
    assert config["model"] == "openai/gpt-5.6-terra"
    assert config["small_model"] == "openai/gpt-5.4-mini"
    assert config["agent"]["model-discovery"]["model"] == "opencode-go-openai-2/glm-5.2"
    assert config["agent"]["model-discovery"]["prompt"] == "{file:./agents/model-discovery.md}"
    assert (OPENCODE / "agents/model-discovery.md").is_file()


def test_live_overlay_extends_the_template_base_config() -> None:
    dockerfile = (OPENCODE.parent / "Dockerfile").read_text()
    assert "OPENCODE_CONFIG=/home/codespace/.config/opencode/opencode.jsonc" in dockerfile


def test_model_discovery_precedes_carrier_and_has_direct_fallback() -> None:
    coordinator = (OPENCODE / "agents/coordinator.md").read_text()
    assert coordinator.index("model-discovery") < coordinator.index("Dispatch through a carrier")
    assert "If discovery returns `CARRIERS:`" in coordinator
    assert "Never infer, construct, or substitute a carrier name." in coordinator
    assert "Do not try a carrier" in coordinator
    assert 'subagent_type="<work-agent>"' in coordinator


def test_carriers_relay_roles() -> None:
    config = load_config()
    for carrier, model in {
        "carrier-go2-glm-5-2": "opencode-go-openai-2/glm-5.2",
        "carrier-go-kimi-k2-7-code": "opencode-go-openai/kimi-k2.7-code",
        "carrier-openai-terra": "openai/gpt-5.6-terra",
    }.items():
        agent = config["agent"][carrier]
        assert agent["model"] == model
        assert agent["prompt"] == "{file:./agents/relay.txt}"
        assert agent["permission"]["task"]["*"] == "allow"
        if model.startswith("opencode-go-"):
            provider, model_id = model.split("/", maxsplit=1)
            assert config["provider"][provider]["models"][model_id]["tool_call"] is True


def test_discovery_probes_go_carriers_and_uses_three_levels() -> None:
    config = load_config()
    discovery = (OPENCODE / "agents/model-discovery.md").read_text()
    assert config["subagent_depth"] == 3
    assert "carrier-go2-glm-5-2" in discovery
    assert "carrier-go-kimi-k2-7-code" in discovery
    assert "Use the read tool" in discovery
    assert "carrier-go2-glm-5-2,carrier-go-kimi-k2-7-code" in discovery


def test_vshn_carriers_are_conditional_and_example_stays_generic() -> None:
    discovery = (OPENCODE / "agents/model-discovery.md").read_text()
    example = (OPENCODE / "untracked-config.example.jsonc").read_text()
    assert "Never return a VSHN carrier until" in discovery
    assert '"model": "my-favorite-model"' in example
    assert '"opencode-go-openai-2": {' in example
    assert '"apiKey": "apiKey"' in example


if __name__ == "__main__":
    test_config_parses_and_loads_markdown_discovery()
    test_model_discovery_precedes_carrier_and_has_direct_fallback()
    test_carriers_relay_roles()
    test_vshn_carriers_are_conditional_and_example_stays_generic()
