import importlib.util
import json
import os
import re
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any, cast
from unittest.mock import patch

MODEL_IDS = [
    "chat",
    "chat_thinking",
    "web_research",
    "translate_de",
    "translate_en",
    "fix_grammar_en",
    "fix_grammar_de",
    "linux_cli",
]
ROUTER_MODEL_IDS = [
    "router-chat",
    "router-chat_thinking",
    "router-web_research",
    "router-translate_de",
    "router-translate_en",
    "router-fix_grammar_en",
    "router-fix_grammar_de",
    "router-linux_cli",
]
MODEL_FAMILIES = ["chat", "chat_thinking", "web_research", "translate", "grammar", "linux_cli"]
SECRET_PLACEHOLDERS = ["BRAVE_API_KEY", "ZEN_API_KEY", "OPENWEBUI_CALLER_KEY", "OPENWEBUI_ADMIN_API_KEY"]
EXTRA_ENV_KEYS = [
    "ENABLE_OPENAI_API",
    "OPENAI_API_BASE_URL",
    "OPENAI_API_KEYS",
    "DEFAULT_MODELS",
    "ENABLE_MODEL_FILTER",
    "MODEL_FILTER_LIST",
]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT_PATH = os.path.join(ROOT, "scripts", "update-openwebui-models.py")
DEPLOY_PATH = os.path.join(ROOT, "deploys", "openwebui", "deploy.py")
COMPOSE_PATH = os.path.join(ROOT, "deploys", "openwebui", "files", "docker-compose.yml")
AISIX_CONFIG_PATH = os.path.join(ROOT, "deploys", "openwebui", "files", "aisix-config.yaml")
RESOURCES_PATH = os.path.join(ROOT, "deploys", "openwebui", "files", "resources.yaml")
ALL_PATH = os.path.join(ROOT, "group_data", "all.py")
CI_PATH = os.path.join(ROOT, "group_data", "ci.py")


def load_module(name: str, path: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_all_module(name: str) -> ModuleType:
    with patch.dict(os.environ, {"CI": ""}):
        return load_module(name, ALL_PATH)


def load_reconciler() -> ModuleType:
    assert os.path.isfile(SCRIPT_PATH)
    return load_module("update_openwebui_models", SCRIPT_PATH)


def require_callable(module: ModuleType, name: str) -> Callable[..., Any]:
    function = cast(Callable[..., Any] | None, getattr(module, name, None))
    assert function is not None
    return function


def group_manifest(openwebui: dict[str, Any]) -> dict[str, Any]:
    return {
        "default_models": openwebui["default_models"],
        "model_map": openwebui["model_map"],
        "presets": openwebui["presets"],
    }


def secret_placeholder_keys_are_commented(path: str) -> None:
    lines = Path(path).read_text().splitlines()
    for key in SECRET_PLACEHOLDERS:
        marker = f'    "{key}": "",'
        index = lines.index(marker)
        assert lines[index - 1].strip().startswith("# Set in local.py"), (key, lines[index - 1])


def test_openwebui_group_data_contract() -> None:
    all_data = load_all_module("openwebui_all")
    openwebui = cast(dict[str, Any], all_data.openwebui)

    assert openwebui["enabled"] is True
    assert openwebui["router_backend"] == "aisix"
    assert openwebui["router_config_path"] == "aisix-config.yaml"
    assert openwebui["router_resources_path"] == "resources.yaml"
    assert openwebui["default_models"] == MODEL_IDS
    assert openwebui["model_map"] == dict(zip(MODEL_IDS, ROUTER_MODEL_IDS, strict=True))
    assert list(openwebui["model_map"]) == MODEL_IDS
    assert all(alias not in MODEL_IDS for alias in openwebui["model_map"].values())
    presets = cast(list[dict[str, Any]], openwebui["presets"])
    assert [preset["id"] for preset in presets] == MODEL_IDS
    assert [preset["name"] for preset in presets] == [
        "Chat",
        "Chat (Thinking)",
        "Web Research",
        "Translate to German",
        "Translate to English",
        "Fix English Grammar",
        "Fix German Grammar",
        "Linux CLI",
    ]
    assert [preset["web_search"] for preset in presets] == [False, False, True, False, False, False, False, False]
    assert all(preset["system"] for preset in presets)
    assert list(openwebui["extra_env"]) == EXTRA_ENV_KEYS
    assert openwebui["extra_env"]["OPENAI_API_KEYS"] == "${OPENWEBUI_CALLER_KEY}"
    assert openwebui["extra_env"]["OPENAI_API_BASE_URL"] == openwebui["openai_compatible_base_url"]
    assert openwebui["openai_compatible_base_url"] == "http://aisix:3000/v1"
    joined = ",".join(MODEL_IDS)
    assert openwebui["extra_env"]["DEFAULT_MODELS"] == joined
    assert openwebui["extra_env"]["MODEL_FILTER_LIST"] == joined
    for provider in ("zen", "ollama"):
        models = cast(dict[str, str], openwebui[provider]["models"])
        assert list(models) == MODEL_FAMILIES
        assert all(models.values())
    assert openwebui["zen"]["base_url"] == "https://opencode.ai/zen/go/v1"
    assert openwebui["ollama"]["base_url"] == "http://host.docker.internal:11434/v1"
    for key in SECRET_PLACEHOLDERS:
        assert openwebui[key] == ""
    assert openwebui["OLLAMA_API_KEY"] == "ollama"
    secret_placeholder_keys_are_commented(ALL_PATH)


def test_openwebui_ci_group_data_mirrors_non_secret_values() -> None:
    all_data = load_all_module("openwebui_all_mirror")
    ci_data = load_module("openwebui_ci", CI_PATH)
    all_openwebui = cast(dict[str, Any], all_data.openwebui)
    ci_openwebui = cast(dict[str, Any], ci_data.openwebui)

    assert ci_openwebui["enabled"] is False
    expected = {key: value for key, value in all_openwebui.items() if key not in SECRET_PLACEHOLDERS}
    expected["enabled"] = False
    assert ci_openwebui == expected
    assert json.dumps(ci_openwebui, sort_keys=True) == json.dumps(expected, sort_keys=True)
    for key in SECRET_PLACEHOLDERS:
        assert key not in ci_openwebui


def test_compose_renders_aisix_gateway_and_openwebui_contract(tmp_path: Path) -> None:
    shutil.copy(COMPOSE_PATH, tmp_path / "docker-compose.yml")
    environment = {
        "AISIX_VERSION": "1.4.0",
        "ZEN_API_KEY": "test-zen-key",
        "ZEN_API_BASE": "https://example.invalid/zen/v1",
        "OLLAMA_API_KEY": "test-ollama-key",
        "OLLAMA_API_BASE": "http://host.docker.internal:11434/v1",
        "OPENWEBUI_CALLER_KEY": "test-caller-key",
        "ENABLE_OPENAI_API": "true",
        "OPENAI_API_BASE_URL": "http://aisix:3000/v1",
        "OPENAI_API_KEYS": "test-caller-key",
        "DEFAULT_MODELS": ",".join(MODEL_IDS),
        "ENABLE_MODEL_FILTER": "true",
        "MODEL_FILTER_LIST": ",".join(MODEL_IDS),
    }
    for provider in ("ZEN", "OLLAMA"):
        for family in MODEL_FAMILIES:
            environment[f"{provider}_{family.upper()}_MODEL"] = f"test-{provider.lower()}-{family}"
    (tmp_path / ".env").write_text("".join(f"{key}={value}\n" for key, value in environment.items()))
    result = subprocess.run(
        ["docker", "compose", "config", "--format", "json"],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    services = json.loads(result.stdout)["services"]

    assert list(services) == ["aisix", "open-webui", "searxng"]
    aisix = services["aisix"]
    assert aisix["image"] == "ghcr.io/api7/aisix:1.4.0"
    assert aisix["expose"] == ["3000"]
    assert "ports" not in aisix
    assert aisix["restart"] == "unless-stopped"
    mounts = {mount["target"]: mount for mount in aisix["volumes"]}
    assert set(mounts) == {"/etc/aisix/config.yaml", "/etc/aisix/resources.yaml"}
    for mount in mounts.values():
        assert mount["read_only"] is True
    aisix_env = aisix["environment"]
    for key in ("ZEN_API_KEY", "ZEN_API_BASE", "OLLAMA_API_KEY", "OLLAMA_API_BASE", "OPENWEBUI_CALLER_KEY"):
        assert aisix_env[key] == environment[key]
    for provider in ("ZEN", "OLLAMA"):
        for family in MODEL_FAMILIES:
            assert aisix_env[f"{provider}_{family.upper()}_MODEL"] == environment[f"{provider}_{family.upper()}_MODEL"]

    openwebui_env = services["open-webui"]["environment"]
    assert openwebui_env["WEBUI_AUTH"] == "False"
    assert openwebui_env["DATABASE_ENABLE_SESSION_SHARING"] == "True"
    assert openwebui_env["ENABLE_API_KEYS"].lower() == "true"
    assert openwebui_env["ENABLE_OPENAI_API"] == "true"
    assert openwebui_env["OPENAI_API_BASE_URL"] == "http://aisix:3000/v1"
    assert openwebui_env["OPENAI_API_KEYS"] == "test-caller-key"
    assert openwebui_env["DEFAULT_MODELS"] == ",".join(MODEL_IDS)
    assert openwebui_env["ENABLE_MODEL_FILTER"] == "true"
    assert openwebui_env["MODEL_FILTER_LIST"] == ",".join(MODEL_IDS)
    assert services["open-webui"]["image"] == "ghcr.io/open-webui/open-webui:v0.11.4"

    compose_text = Path(COMPOSE_PATH).read_text()
    for source in re.findall(r'- "([^":]+):', compose_text):
        assert ".." not in source
        assert not source.startswith("/")
    for required in (
        "ZEN_API_KEY:?ZEN_API_KEY is required",
        "ZEN_API_BASE:?ZEN_API_BASE is required",
        "OPENWEBUI_CALLER_KEY:?OPENWEBUI_CALLER_KEY is required",
        "OPENAI_API_KEYS:?OPENAI_API_KEYS is required",
    ):
        assert required in compose_text
    assert re.search(r"^services:\n  aisix:", compose_text, re.MULTILINE)
    assert "networks:" not in compose_text
    assert compose_text.startswith("---\n")


def test_aisix_resources_validate_with_nonsecret_environment(tmp_path: Path) -> None:
    resources_text = Path(RESOURCES_PATH).read_text()
    names = set(re.findall(r"\$\{([A-Z_][A-Z0-9_]*)\}", resources_text))
    names.update(re.findall(r"^\s*key_env:\s*([A-Z_][A-Z0-9_]*)\s*$", resources_text, re.MULTILINE))
    variables = sorted(names)
    assert variables
    assert "ZEN_API_KEY" in variables
    assert "OPENCODE_GO_API_KEY" not in variables
    command = [
        "docker",
        "run",
        "--rm",
        "--entrypoint",
        "/usr/local/bin/aisix",
    ]
    for variable in variables:
        command.extend(["-e", f"{variable}=sample-{variable.lower()}"])
    command.extend(
        [
            "--volume",
            f"{RESOURCES_PATH}:/etc/aisix/resources.yaml:ro",
            "ghcr.io/api7/aisix:1.4.0",
            "validate",
            "--resources",
            "/etc/aisix/resources.yaml",
        ]
    )
    result = subprocess.run(command, check=False, capture_output=True, text=True)
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "loaded 23 resource(s)" in output

    mutated = resources_text.replace("      strategy: failover\n", "      strategy: not-a-strategy\n")
    assert mutated != resources_text
    mutated_path = tmp_path / "resources-mutated.yaml"
    mutated_path.write_text(mutated)
    mutated_command = command.copy()
    mutated_command[mutated_command.index("--volume") + 1] = f"{mutated_path}:/etc/aisix/resources.yaml:ro"
    mutated_result = subprocess.run(mutated_command, check=False, capture_output=True, text=True)
    assert mutated_result.returncode == 1, mutated_result.stdout + mutated_result.stderr
    assert "schema validation failed" in mutated_result.stderr
