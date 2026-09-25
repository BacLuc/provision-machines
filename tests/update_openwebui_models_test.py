import copy
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
from collections.abc import Callable
from email.message import Message
from pathlib import Path
from types import ModuleType
from typing import Any, cast
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request

import pytest

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


class FakeResponse:
    def __init__(self, payload: object, status: int = 200) -> None:
        self.payload = payload
        self.status = status

    def read(self) -> bytes:
        return json.dumps(self.payload).encode()

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None


class RecordingOpener:
    def __init__(self, responses: list[object]) -> None:
        self.responses = responses
        self.requests: list[Request] = []

    def __call__(self, request: Request, timeout: float) -> FakeResponse:
        del timeout
        self.requests.append(request)
        response = self.responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return cast(FakeResponse, response)


class ModelApiOpener:
    def __init__(
        self,
        exported: list[dict[str, object]],
        *,
        all_rows: list[dict[str, object]] | None = None,
        sync_status: int = 200,
        sync_response: object | None = None,
    ) -> None:
        self.exported = copy.deepcopy(exported)
        self.all_rows = copy.deepcopy(exported if all_rows is None else all_rows)
        self.sync_status = sync_status
        self.sync_response = sync_response
        self.sync_payloads: list[dict[str, object]] = []
        self.import_payloads: list[dict[str, object]] = []
        self.deleted: list[str] = []
        self.requests: list[Request] = []
        self.paths: list[tuple[str, str]] = []

    def __call__(self, request: Request, timeout: float) -> FakeResponse:
        del timeout
        path = urlparse(request.full_url).path
        self.requests.append(request)
        self.paths.append((request.method or "", path))
        if path == "/ready":
            return FakeResponse({})
        if path == "/api/v1/auths/user":
            return FakeResponse({"id": "admin-user"})
        if path == "/api/v1/auths/signin":
            return FakeResponse({"token": "session-token", "id": "admin-user"})
        if path == "/api/v1/models/export":
            return FakeResponse(copy.deepcopy(self.exported))
        if path == "/api/v1/models/all":
            return FakeResponse(copy.deepcopy(self.all_rows))
        if path == "/api/v1/models/sync":
            assert request.data is not None
            payload = json.loads(cast(bytes, request.data))
            assert isinstance(payload, dict)
            self.sync_payloads.append(cast(dict[str, object], payload))
            if self.sync_status != 200:
                raise HTTPError(request.full_url, self.sync_status, "failed", Message(), io.BytesIO(b"private"))
            models = payload.get("models")
            assert isinstance(models, list)
            if self.sync_response is None:
                self.exported = copy.deepcopy(cast(list[dict[str, object]], models))
                self.all_rows = copy.deepcopy(cast(list[dict[str, object]], models))
                return FakeResponse(copy.deepcopy(self.exported))
            return FakeResponse(self.sync_response)
        if path == "/api/v1/models/import":
            assert request.data is not None
            payload = json.loads(cast(bytes, request.data))
            assert isinstance(payload, dict)
            self.import_payloads.append(cast(dict[str, object], payload))
            models = cast(list[dict[str, object]], payload["models"])
            self.exported.extend(copy.deepcopy(models))
            self.all_rows.extend(copy.deepcopy(models))
            return FakeResponse(True)
        if path == "/api/v1/models/model/delete":
            assert request.data is not None
            payload = json.loads(cast(bytes, request.data))
            assert isinstance(payload, dict)
            model_id = payload["id"]
            assert isinstance(model_id, str)
            self.deleted.append(model_id)
            self.exported = [model for model in self.exported if model.get("id") != model_id]
            self.all_rows = [model for model in self.all_rows if model.get("id") != model_id]
            return FakeResponse(True)
        raise AssertionError(f"unexpected request path: {path}")


def model_row(model_id: str, base_model_id: object, **extra: object) -> dict[str, object]:
    row: dict[str, object] = {
        "id": model_id,
        "user_id": "owner",
        "base_model_id": base_model_id,
        "name": model_id,
        "params": {},
        "meta": {},
        "access_grants": [],
        "is_active": True,
        "updated_at": 1,
        "created_at": 1,
    }
    row.update(extra)
    return row


def test_aisix_parser_returns_router_targets_without_secret_values() -> None:
    reconciler = load_reconciler()
    routes = require_callable(reconciler, "parse_aisix_model_names")(RESOURCES_PATH)

    assert routes == {
        "router-chat": ["zen-chat", "ollama-chat"],
        "router-chat_thinking": ["zen-chat_thinking", "ollama-chat_thinking"],
        "router-web_research": ["zen-web_research", "ollama-web_research"],
        "router-translate_de": ["zen-translate", "ollama-translate"],
        "router-translate_en": ["zen-translate", "ollama-translate"],
        "router-fix_grammar_en": ["zen-grammar", "ollama-grammar"],
        "router-fix_grammar_de": ["zen-grammar", "ollama-grammar"],
        "router-linux_cli": ["zen-linux_cli", "ollama-linux_cli"],
    }
    assert "ZEN_API_KEY" not in repr(routes)
    assert "OPENWEBUI_CALLER_KEY" not in repr(routes)


@pytest.mark.parametrize(
    "replacement",
    [
        ('_format_version: "1"\n', ""),
        ('_format_version: "1"', '_format_version: "2"'),
        ("  - display_name: zen-chat", "\t- display_name: zen-chat"),
        ("display_name: zen-chat", "display_name: &zen zen-chat"),
        ("display_name: zen-chat", "display_name: ${ZEN_CHAT}"),
        ("display_name: router-chat\n", "display_name: router-chat\n  - display_name: router-chat\n"),
        ("      targets:\n", "      targets: [\n"),
        ("      targets:\n", ""),
        ("        - model: zen-chat\n", "        - model: missing-target\n"),
        ("          priority: 100\n", "          priority: ${PRIORITY}\n"),
        ("      strategy: failover\n", "      strategy: round_robin\n"),
        ("      retries: 0\n", "      retries: 1\n"),
        ("    model_name: ${ZEN_CHAT_MODEL}\n", "    unsupported: value\n"),
        ("    provider_key: zen\n", "    provider_key:\n"),
    ],
)
def test_aisix_parser_rejects_unsupported_or_malformed_resources(tmp_path: Path, replacement: tuple[str, str]) -> None:
    reconciler = load_reconciler()
    parse = require_callable(reconciler, "parse_aisix_model_names")
    text = Path(RESOURCES_PATH).read_text()
    assert replacement[0] in text
    resources_path = tmp_path / "resources.yaml"
    resources_path.write_text(text.replace(replacement[0], replacement[1], 1))

    with pytest.raises(ValueError):
        parse(resources_path)


def test_manifest_loader_rejects_wrong_order_secrets_and_alias_collision(tmp_path: Path) -> None:
    reconciler = load_reconciler()
    load_manifest = require_callable(reconciler, "load_manifest")
    parse = require_callable(reconciler, "parse_aisix_model_names")
    validate = require_callable(reconciler, "validate_router_models")
    all_data = load_all_module("manifest_source")
    manifest = group_manifest(cast(dict[str, Any], all_data.openwebui))
    routes = parse(RESOURCES_PATH)

    def write(name: str, value: object) -> Path:
        path = tmp_path / name
        path.write_text(json.dumps(value))
        return path

    assert load_manifest(write("manifest.json", manifest)) == manifest
    validate(load_manifest(write("manifest.json", manifest)), routes)

    reversed_defaults = dict(manifest)
    reversed_defaults["default_models"] = list(reversed(MODEL_IDS))
    with pytest.raises(ValueError):
        load_manifest(write("reversed.json", reversed_defaults))

    missing_preset = dict(manifest)
    missing_preset["presets"] = manifest["presets"][:-1]
    with pytest.raises(ValueError):
        load_manifest(write("missing.json", missing_preset))

    secret_manifest = json.loads(json.dumps(manifest))
    secret_manifest["presets"][0]["api_key"] = "secret"
    with pytest.raises(ValueError):
        load_manifest(write("secret.json", secret_manifest))

    alias_equals_id = json.loads(json.dumps(manifest))
    alias_equals_id["model_map"]["chat"] = "chat"
    with pytest.raises(ValueError):
        validate(load_manifest(write("alias.json", alias_equals_id)), routes)

    duplicate_alias = json.loads(json.dumps(manifest))
    duplicate_alias["model_map"]["chat_thinking"] = duplicate_alias["model_map"]["chat"]
    with pytest.raises(ValueError):
        validate(load_manifest(write("duplicate.json", duplicate_alias)), routes)

    unknown_alias = json.loads(json.dumps(manifest))
    unknown_alias["model_map"]["chat"] = "router-missing"
    with pytest.raises(ValueError):
        validate(load_manifest(write("unknown.json", unknown_alias)), routes)


def test_build_models_matches_eight_fixed_payload_contract() -> None:
    reconciler = load_reconciler()
    build_models = require_callable(reconciler, "build_models")
    all_data = load_all_module("payload_source")
    manifest = group_manifest(cast(dict[str, Any], all_data.openwebui))
    specs = [
        ("chat", "Chat", "You are a helpful assistant.", False),
        ("chat_thinking", "Chat (Thinking)", "Think carefully before answering.", False),
        ("web_research", "Web Research", "Research answers with web search and cite the sources.", True),
        (
            "translate_de",
            "Translate to German",
            "Translate the user's text into German and return only the translation.",
            False,
        ),
        (
            "translate_en",
            "Translate to English",
            "Translate the user's text into English and return only the translation.",
            False,
        ),
        ("fix_grammar_en", "Fix English Grammar", "Correct English grammar and preserve the original meaning.", False),
        ("fix_grammar_de", "Fix German Grammar", "Correct German grammar and preserve the original meaning.", False),
        ("linux_cli", "Linux CLI", "Help with Linux command-line tasks and return safe, practical commands.", False),
    ]
    expected = []
    for model_id, name, system, web_search in specs:
        params: dict[str, object] = {"system": system}
        if web_search:
            params["function_calling"] = "native"
        expected.append(
            {
                "id": model_id,
                "user_id": "admin-user",
                "base_model_id": cast(dict[str, str], manifest["model_map"])[model_id],
                "name": name,
                "params": params,
                "meta": {
                    "capabilities": {
                        "vision": False,
                        "citations": web_search,
                        "web_search": web_search,
                        "image_generation": False,
                        "code_interpreter": False,
                    },
                    "defaultFeatureIds": ["web_search"] if web_search else [],
                    "builtinTools": {"web_search": web_search},
                },
                "access_grants": [],
                "is_active": True,
                "updated_at": 1700000000,
                "created_at": 1700000000,
            }
        )

    assert build_models(manifest, [], user_id="admin-user", now=1700000000) == expected
    web_search_model = next(model for model in expected if model["id"] == "web_research")
    assert cast(dict[str, object], web_search_model["params"])["function_calling"] == "native"
    assert [model["id"] for model in expected if "function_calling" in cast(dict[str, object], model["params"])] == [
        "web_research"
    ]


def test_build_models_preserves_existing_fields_and_rejects_collision() -> None:
    reconciler = load_reconciler()
    build_models = require_callable(reconciler, "build_models")
    all_data = load_all_module("preserve_source")
    manifest = group_manifest(cast(dict[str, Any], all_data.openwebui))
    existing = [model_row("chat", "router-chat", user_id="owner", updated_at=10, created_at=11)]

    models = build_models(manifest, existing, user_id="admin-user", now=20)
    assert models[0]["user_id"] == "owner"
    assert models[0]["updated_at"] == 10
    assert models[0]["created_at"] == 11

    with pytest.raises(ValueError):
        build_models(manifest, [model_row("chat", None)], user_id="admin-user", now=20)
    with pytest.raises(ValueError):
        build_models(manifest, [model_row("chat", "gpt-4")], user_id="admin-user", now=20)


def test_build_sync_payload_preserves_base_null_and_unrelated_rows_only() -> None:
    reconciler = load_reconciler()
    build_sync_payload = require_callable(reconciler, "build_sync_payload")
    all_data = load_all_module("sync_source")
    manifest = group_manifest(cast(dict[str, Any], all_data.openwebui))
    base_null = model_row("base_override", None)
    unrelated = model_row("custom_model", "gpt-4")
    stale = model_row("old_chat", "router-chat")

    payload = build_sync_payload(manifest, [base_null, unrelated, stale], user_id="admin-user", now=2)

    assert [model["id"] for model in payload[:8]] == MODEL_IDS
    assert [model["id"] for model in payload[8:]] == ["base_override", "custom_model"]
    assert all(model.get("base_model_id") not in {"router-chat"} for model in payload[8:])


def test_verify_models_reports_missing_managed_id_and_changed_order() -> None:
    reconciler = load_reconciler()
    build_models = require_callable(reconciler, "build_models")
    verify_models = require_callable(reconciler, "verify_models")
    all_data = load_all_module("verify_missing_source")
    manifest = group_manifest(cast(dict[str, Any], all_data.openwebui))
    expected = build_models(manifest, [], user_id="admin-user", now=1)

    with pytest.raises(RuntimeError, match="missing"):
        verify_models(expected, [expected[0], {"id": "extra", "base_model_id": None}])

    with pytest.raises(RuntimeError, match="order"):
        verify_models(expected, list(reversed(expected)))

    actual = copy.deepcopy(expected)
    actual[0]["meta"]["description"] = "server default"
    actual[0]["updated_at"] = 2
    verify_models(expected, actual)


def test_read_env_file_requires_private_mode_and_valid_lines(tmp_path: Path) -> None:
    reconciler = load_reconciler()
    read_env_file = require_callable(reconciler, "read_env_file")
    env_path = tmp_path / ".env"
    env_path.write_text('OPENWEBUI_ADMIN_API_KEY="test-secret"\n# comment\nEMPTY=\n')
    env_path.chmod(0o600)
    assert read_env_file(env_path) == {"OPENWEBUI_ADMIN_API_KEY": "test-secret", "EMPTY": ""}

    env_path.chmod(0o644)
    with pytest.raises(PermissionError):
        read_env_file(env_path)
    env_path.chmod(0o600)

    env_path.write_text("no-equals-sign\n")
    with pytest.raises(ValueError):
        read_env_file(env_path)

    env_path.write_text("9BAD=value\n")
    with pytest.raises(ValueError):
        read_env_file(env_path)


def test_request_json_does_not_expose_error_body_or_secret_headers() -> None:
    reconciler = load_reconciler()
    request_json = require_callable(reconciler, "request_json")
    error = HTTPError(
        "http://127.0.0.1:13307/api/v1/models/sync",
        401,
        "Unauthorized",
        Message(),
        io.BytesIO(b'{"token":"super-secret"}'),
    )
    opener = RecordingOpener([error])

    with pytest.raises(RuntimeError) as raised:
        request_json("GET", "http://127.0.0.1:13307/api/v1/models/export", opener=opener, attempts=1)

    assert getattr(raised.value, "status", None) == 401
    assert "super-secret" not in str(raised.value)


def test_request_json_retries_transient_status_and_url_errors() -> None:
    reconciler = load_reconciler()
    request_json = require_callable(reconciler, "request_json")
    opener = RecordingOpener(
        [
            HTTPError("http://127.0.0.1:13307/x", 429, "busy", Message(), io.BytesIO(b"{}")),
            URLError("down"),
            FakeResponse({"ok": True}),
        ]
    )
    sleeps: list[float] = []

    assert request_json("GET", "http://127.0.0.1:13307/x", opener=opener, sleep=sleeps.append) == {"ok": True}
    assert sleeps == [1.0, 2.0]

    failing = RecordingOpener([HTTPError("http://127.0.0.1:13307/x", 500, "boom", Message(), io.BytesIO(b"{}"))])
    with pytest.raises(RuntimeError):
        request_json("GET", "http://127.0.0.1:13307/x", opener=failing, attempts=1)


def test_authenticate_uses_admin_api_key_header_without_exposing_it_in_request_line() -> None:
    reconciler = load_reconciler()
    authenticate = require_callable(reconciler, "authenticate")
    opener = RecordingOpener([FakeResponse({"id": "admin-user"})])

    headers, user_id = authenticate(
        "http://127.0.0.1:13307",
        {"OPENWEBUI_ADMIN_API_KEY": "admin-secret"},
        opener=opener,
    )

    assert user_id == "admin-user"
    assert headers == {"x-api-key": "admin-secret"}
    request = opener.requests[0]
    assert request.full_url == "http://127.0.0.1:13307/api/v1/auths/user"
    assert "admin-secret" not in request.full_url
    assert request.get_header("X-api-key") == "admin-secret"


def test_authenticate_signs_in_then_verifies_the_session_token() -> None:
    reconciler = load_reconciler()
    authenticate = require_callable(reconciler, "authenticate")
    opener = RecordingOpener(
        [
            FakeResponse({"token": "session-token", "id": "admin-user"}),
            FakeResponse({"id": "admin-user"}),
        ]
    )

    headers, user_id = authenticate("http://127.0.0.1:13307", {}, opener=opener)

    assert user_id == "admin-user"
    assert headers == {"Authorization": "Bearer session-token"}
    paths = [urlparse(request.full_url).path for request in opener.requests]
    assert paths == ["/api/v1/auths/signin", "/api/v1/auths/user"]
    assert all("session-token" not in request.full_url for request in opener.requests)
    signin = opener.requests[0]
    assert signin.data is not None
    assert json.loads(cast(bytes, signin.data)) == {"email": "", "password": ""}
    assert opener.requests[1].get_header("Authorization") == "Bearer session-token"


def test_wait_ready_retries_transient_failures_with_bounded_backoff() -> None:
    reconciler = load_reconciler()
    wait_ready = require_callable(reconciler, "wait_ready")
    opener = RecordingOpener([URLError("not ready"), URLError("not ready"), FakeResponse({})])
    sleeps: list[float] = []

    wait_ready(
        "http://127.0.0.1:13307",
        {},
        attempts=3,
        backoff=0.5,
        opener=opener,
        sleep=sleeps.append,
    )

    assert len(opener.requests) == 3
    assert sleeps == [0.5, 1.0]

    capped = RecordingOpener([URLError("not ready") for _ in range(6)])
    capped_sleeps: list[float] = []
    with pytest.raises(RuntimeError):
        wait_ready(
            "http://127.0.0.1:13307",
            {},
            attempts=6,
            backoff=5,
            opener=capped,
            sleep=capped_sleeps.append,
        )
    assert max(capped_sleeps) <= 30


def reconcile_env(tmp_path: Path) -> Path:
    env_path = tmp_path / ".env"
    env_path.write_text("OPENWEBUI_ADMIN_API_KEY=admin-secret\n")
    env_path.chmod(0o600)
    return env_path


def test_reconcile_uses_model_all_for_preservation_and_export_pre_post(tmp_path: Path) -> None:
    reconciler = load_reconciler()
    reconcile = require_callable(reconciler, "reconcile")
    all_data = load_all_module("reconcile_source")
    manifest = group_manifest(cast(dict[str, Any], all_data.openwebui))
    base_null = model_row("base_override", None)
    unrelated = model_row("custom_model", "gpt-4")
    opener = ModelApiOpener([unrelated], all_rows=[base_null, unrelated])

    result = reconcile(
        "http://127.0.0.1:13307",
        manifest,
        RESOURCES_PATH,
        reconcile_env(tmp_path),
        opener=opener,
        sleep=lambda _seconds: None,
        now=1700000000,
    )

    assert [model["id"] for model in result] == MODEL_IDS + ["base_override", "custom_model"]
    sync_models = cast(list[dict[str, object]], opener.sync_payloads[0]["models"])
    assert [model["id"] for model in sync_models] == MODEL_IDS + ["base_override", "custom_model"]
    assert opener.paths.count(("GET", "/api/v1/models/export")) == 2
    assert opener.paths.count(("GET", "/api/v1/models/all")) == 1
    assert opener.paths[0] == ("GET", "/ready")
    assert opener.paths[1] == ("GET", "/api/v1/auths/user")
    assert opener.sync_payloads[0]["models"] == result
    assert opener.import_payloads == []
    assert opener.deleted == []


def test_reconcile_detects_collision_visible_only_in_model_all(tmp_path: Path) -> None:
    reconciler = load_reconciler()
    reconcile = require_callable(reconciler, "reconcile")
    all_data = load_all_module("collision_source")
    manifest = group_manifest(cast(dict[str, Any], all_data.openwebui))
    opener = ModelApiOpener([], all_rows=[model_row("chat", None)])

    with pytest.raises(ValueError):
        reconcile(
            "http://127.0.0.1:13307",
            manifest,
            RESOURCES_PATH,
            reconcile_env(tmp_path),
            opener=opener,
            sleep=lambda _seconds: None,
            now=1700000000,
        )

    assert opener.sync_payloads == []
    assert opener.import_payloads == []


def test_reconcile_is_idempotent_across_runs(tmp_path: Path) -> None:
    reconciler = load_reconciler()
    reconcile = require_callable(reconciler, "reconcile")
    all_data = load_all_module("idempotent_source")
    manifest = group_manifest(cast(dict[str, Any], all_data.openwebui))
    env_path = reconcile_env(tmp_path)
    opener = ModelApiOpener([])

    first = reconcile(
        "http://127.0.0.1:13307", manifest, RESOURCES_PATH, env_path, opener=opener, sleep=lambda _s: None, now=1
    )
    second = reconcile(
        "http://127.0.0.1:13307", manifest, RESOURCES_PATH, env_path, opener=opener, sleep=lambda _s: None, now=1
    )

    assert [model["id"] for model in first] == MODEL_IDS
    assert second == first
    assert len(opener.sync_payloads) == 2
    assert opener.sync_payloads[0] == opener.sync_payloads[1]
    assert opener.import_payloads == []
    assert opener.deleted == []


def test_reconcile_signs_in_when_no_admin_key_is_configured(tmp_path: Path) -> None:
    reconciler = load_reconciler()
    reconcile = require_callable(reconciler, "reconcile")
    all_data = load_all_module("reconcile_no_key_source")
    manifest = group_manifest(cast(dict[str, Any], all_data.openwebui))
    env_path = tmp_path / ".env"
    env_path.write_text("OPENWEBUI_ADMIN_API_KEY=\n")
    env_path.chmod(0o600)
    opener = ModelApiOpener([])

    reconcile(
        "http://127.0.0.1:13307",
        manifest,
        RESOURCES_PATH,
        env_path,
        opener=opener,
        sleep=lambda _seconds: None,
        now=1700000000,
    )

    assert opener.paths[1] == ("POST", "/api/v1/auths/signin")
    assert opener.paths[2] == ("GET", "/api/v1/auths/user")
    export_request = next(request for request in opener.requests if urlparse(request.full_url).path.endswith("/export"))
    assert export_request.get_header("Authorization") == "Bearer session-token"
    assert all("session-token" not in request.full_url for request in opener.requests)


@pytest.mark.parametrize("status", [400, 401, 422])
def test_reconcile_treats_sync_auth_and_schema_errors_as_terminal(tmp_path: Path, status: int) -> None:
    reconciler = load_reconciler()
    reconcile = require_callable(reconciler, "reconcile")
    all_data = load_all_module(f"terminal_{status}_source")
    manifest = group_manifest(cast(dict[str, Any], all_data.openwebui))
    opener = ModelApiOpener([], sync_status=status)

    with pytest.raises(RuntimeError) as raised:
        reconcile(
            "http://127.0.0.1:13307",
            manifest,
            RESOURCES_PATH,
            reconcile_env(tmp_path),
            opener=opener,
            sleep=lambda _seconds: None,
            now=1700000000,
        )

    assert getattr(raised.value, "status", None) == status
    assert opener.import_payloads == []


def test_reconcile_rejects_empty_sync_response(tmp_path: Path) -> None:
    reconciler = load_reconciler()
    reconcile = require_callable(reconciler, "reconcile")
    all_data = load_all_module("empty_sync_source")
    manifest = group_manifest(cast(dict[str, Any], all_data.openwebui))
    opener = ModelApiOpener([], sync_response=[])

    with pytest.raises(RuntimeError, match="empty"):
        reconcile(
            "http://127.0.0.1:13307",
            manifest,
            RESOURCES_PATH,
            reconcile_env(tmp_path),
            opener=opener,
            sleep=lambda _seconds: None,
            now=1700000000,
        )

    assert opener.import_payloads == []


def test_reconcile_rejects_sync_response_id_mismatch(tmp_path: Path) -> None:
    reconciler = load_reconciler()
    reconcile = require_callable(reconciler, "reconcile")
    all_data = load_all_module("sync_mismatch_source")
    manifest = group_manifest(cast(dict[str, Any], all_data.openwebui))
    opener = ModelApiOpener([], sync_response=[{"id": "chat"}])

    with pytest.raises(RuntimeError, match="match"):
        reconcile(
            "http://127.0.0.1:13307",
            manifest,
            RESOURCES_PATH,
            reconcile_env(tmp_path),
            opener=opener,
            sleep=lambda _seconds: None,
            now=1700000000,
        )

    assert opener.import_payloads == []


@pytest.mark.parametrize("status", [404, 405, 501])
def test_reconcile_import_fallback_deletes_stale_alias_rows_only(tmp_path: Path, status: int) -> None:
    reconciler = load_reconciler()
    reconcile = require_callable(reconciler, "reconcile")
    all_data = load_all_module(f"fallback_{status}_source")
    manifest = group_manifest(cast(dict[str, Any], all_data.openwebui))
    stale = model_row("zz_stale_probe", "router-chat")
    base_null = model_row("base_override", None)
    unrelated = model_row("custom_model", "gpt-4")
    opener = ModelApiOpener([stale, base_null, unrelated], sync_status=status)

    result = reconcile(
        "http://127.0.0.1:13307",
        manifest,
        RESOURCES_PATH,
        reconcile_env(tmp_path),
        opener=opener,
        sleep=lambda _seconds: None,
        now=1700000000,
    )

    assert {model["id"] for model in result} == set(MODEL_IDS + ["base_override", "custom_model"])
    assert [model["id"] for model in result if model["id"] in MODEL_IDS] == MODEL_IDS
    assert len(opener.import_payloads) == 1
    imported_models = cast(list[dict[str, object]], opener.import_payloads[0]["models"])
    assert [model["id"] for model in imported_models] == MODEL_IDS
    assert opener.deleted == ["zz_stale_probe"]


def test_cli_uses_default_url_and_passes_manifest_paths(tmp_path: Path) -> None:
    reconciler = load_reconciler()
    main = require_callable(reconciler, "main")
    all_data = load_all_module("cli_source")
    manifest = group_manifest(cast(dict[str, Any], all_data.openwebui))
    manifest_path = tmp_path / "openwebui-models.json"
    manifest_path.write_text(json.dumps(manifest))
    env_path = reconcile_env(tmp_path)
    calls: list[tuple[str, str, str]] = []

    def fake_reconcile(
        url: str, loaded_manifest: dict[str, object], resources: Path, env: Path
    ) -> list[dict[str, object]]:
        del loaded_manifest
        calls.append((url, str(resources), str(env)))
        return []

    vars(reconciler)["reconcile"] = fake_reconcile
    assert (
        main(
            [
                "--manifest",
                str(manifest_path),
                "--resources",
                RESOURCES_PATH,
                "--env-file",
                str(env_path),
            ]
        )
        == 0
    )
    assert calls == [("http://127.0.0.1:13307", RESOURCES_PATH, str(env_path))]

    calls.clear()
    assert (
        main(
            [
                "--url",
                "http://127.0.0.1:9999",
                "--manifest",
                str(manifest_path),
                "--resources",
                RESOURCES_PATH,
                "--env-file",
                str(env_path),
            ]
        )
        == 0
    )
    assert calls[0][0] == "http://127.0.0.1:9999"


def test_cli_failure_exit_code_without_secret_leakage(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    reconciler = load_reconciler()
    main = require_callable(reconciler, "main")
    all_data = load_all_module("cli_failure_source")
    manifest = group_manifest(cast(dict[str, Any], all_data.openwebui))
    manifest_path = tmp_path / "openwebui-models.json"
    manifest_path.write_text(json.dumps(manifest))
    env_path = reconcile_env(tmp_path)

    def fail_reconcile(*_args: object, **_kwargs: object) -> list[dict[str, object]]:
        error_type = cast(type[Exception], vars(reconciler)["ReconciliationError"])
        raise error_type("token=admin-secret")

    vars(reconciler)["reconcile"] = fail_reconcile
    assert (
        main(
            [
                "--manifest",
                str(manifest_path),
                "--resources",
                RESOURCES_PATH,
                "--env-file",
                str(env_path),
            ]
        )
        == 1
    )
    captured = capsys.readouterr()
    assert "admin-secret" not in captured.err
    assert "admin-secret" not in captured.out
