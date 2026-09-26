import ast
import importlib.util
import itertools
import json
import os
import shlex
import sys
import types
from pathlib import Path
from typing import Any
from urllib.error import URLError

import pytest

_SCRIPT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "scripts",
    "update-openwebui-models.py",
)
_spec = importlib.util.spec_from_file_location("update_openwebui_models", _SCRIPT)
assert _spec is not None
assert _spec.loader is not None
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)

_RESOURCES = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "deploys",
    "openwebui",
    "files",
    "resources.yaml",
)

MODEL_MAP = {
    "chat": "router-chat",
    "chat_thinking": "router-chat-thinking",
    "web_research": "router-web-research",
    "translate_de": "router-translate-de",
    "translate_en": "router-translate-en",
    "fix_grammar_en": "router-fix-grammar-en",
    "fix_grammar_de": "router-fix-grammar-de",
    "linux_cli": "router-linux-cli",
}
DEFAULT_MODELS = [
    "chat",
    "chat_thinking",
    "web_research",
    "translate_de",
    "translate_en",
    "fix_grammar_en",
    "fix_grammar_de",
    "linux_cli",
]
EXPECTED_NAMES = {
    "chat": "Chat",
    "chat_thinking": "Chat (Thinking)",
    "web_research": "Web Research",
    "translate_de": "Translate to German",
    "translate_en": "Translate to English",
    "fix_grammar_en": "Fix English Grammar",
    "fix_grammar_de": "Fix German Grammar",
    "linux_cli": "Linux CLI",
}


def test_build_preset_specs_all_eight() -> None:
    specs = mod.build_preset_specs(MODEL_MAP, DEFAULT_MODELS)
    assert [s["id"] for s in specs] == DEFAULT_MODELS
    for spec in specs:
        assert spec["base_model_id"] == MODEL_MAP[spec["id"]]
        assert spec["name"] == EXPECTED_NAMES[spec["id"]]
        assert spec["id"] != spec["base_model_id"]


def test_build_preset_specs_rejects_id_collision() -> None:
    bad_map = dict(MODEL_MAP)
    bad_map["chat"] = "chat"
    with pytest.raises(ValueError):
        mod.build_preset_specs(bad_map, DEFAULT_MODELS)


def test_build_preset_specs_rejects_unknown_preset() -> None:
    with pytest.raises(ValueError):
        mod.build_preset_specs(MODEL_MAP, ["chat", "unknown"])


def test_build_preset_specs_rejects_missing_map_entry() -> None:
    with pytest.raises(ValueError):
        mod.build_preset_specs({"chat": "router-chat"}, DEFAULT_MODELS)


def test_sync_payload_exact_shape() -> None:
    specs = mod.build_preset_specs(MODEL_MAP, DEFAULT_MODELS)
    now = 1790288638
    models = [mod.to_sync_model(spec, "admin", now) for spec in specs]
    payload = {"models": models}
    assert list(payload["models"][0].keys()) == [
        "id",
        "user_id",
        "base_model_id",
        "name",
        "params",
        "meta",
        "access_grants",
        "is_active",
        "updated_at",
        "created_at",
    ]
    assert [m["id"] for m in payload["models"]] == DEFAULT_MODELS
    assert [m["base_model_id"] for m in payload["models"]] == [MODEL_MAP[p] for p in DEFAULT_MODELS]
    assert [m["name"] for m in payload["models"]] == [EXPECTED_NAMES[p] for p in DEFAULT_MODELS]
    for model in payload["models"]:
        assert model["user_id"] == "admin"
        assert model["access_grants"] == []
        assert model["is_active"] is True
        assert model["updated_at"] == now
        assert model["created_at"] == now


def test_web_research_payload() -> None:
    specs = mod.build_preset_specs(MODEL_MAP, DEFAULT_MODELS)
    model = mod.to_sync_model(next(s for s in specs if s["id"] == "web_research"), "admin", 1790288638)
    assert model["params"]["system"] == mod.PRESET_SYSTEM_PROMPTS["web_research"]
    assert model["params"]["function_calling"] == "native"
    assert set(model["meta"]["capabilities"]) == set(mod.CAPABILITY_KEYS)
    assert model["meta"]["capabilities"]["web_search"] is True
    assert all(v is False for k, v in model["meta"]["capabilities"].items() if k != "web_search")
    assert model["meta"]["defaultFeatureIds"] == ["web_search"]
    assert model["meta"]["builtinTools"] == {"web_search": True}


def test_non_web_research_payload_explicit_capabilities() -> None:
    specs = mod.build_preset_specs(MODEL_MAP, DEFAULT_MODELS)
    for spec in specs:
        if spec["id"] == "web_research":
            continue
        model = mod.to_sync_model(spec, "admin", 1790288638)
        assert isinstance(model["params"]["system"], str) and model["params"]["system"]
        assert "function_calling" not in model["params"]
        assert set(model["meta"]["capabilities"]) == set(mod.CAPABILITY_KEYS)
        assert all(v is False for v in model["meta"]["capabilities"].values())
        assert "defaultFeatureIds" not in model["meta"]
        assert "builtinTools" not in model["meta"]


def test_preset_system_prompts_non_empty_and_distinct() -> None:
    specs = mod.build_preset_specs(MODEL_MAP, DEFAULT_MODELS)
    prompts = [mod.to_sync_model(spec, "admin", 1790288638)["params"]["system"] for spec in specs]
    assert all(isinstance(p, str) and p for p in prompts)
    assert len(set(prompts)) == len(prompts)


def test_parse_aisix_model_names_returns_eight_aliases() -> None:
    with open(_RESOURCES) as f:
        aliases = mod.parse_aisix_model_names(f.read())
    assert [name for name, _ in aliases] == [
        "router-chat",
        "router-chat-thinking",
        "router-web-research",
        "router-translate-de",
        "router-translate-en",
        "router-fix-grammar-en",
        "router-fix-grammar-de",
        "router-linux-cli",
    ]
    for _, targets in aliases:
        assert targets == ["zen-chat", "ollama-chat"]


def test_parse_aisix_model_names_rejects_tabs() -> None:
    with pytest.raises(ValueError):
        mod.parse_aisix_model_names("models:\n\t- display_name: x\n")


def test_parse_aisix_model_names_rejects_flow_style() -> None:
    with pytest.raises(ValueError):
        mod.parse_aisix_model_names("models: [{display_name: x}]\n")


def test_parse_aisix_model_names_rejects_duplicate_keys() -> None:
    with pytest.raises(ValueError):
        mod.parse_aisix_model_names("models:\n  - display_name: a\n    display_name: b\n")


def test_parse_aisix_model_names_rejects_missing_models() -> None:
    with pytest.raises(ValueError):
        mod.parse_aisix_model_names("api_keys:\n  - display_name: k\n")


def test_read_env_file_parses_values(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("# comment\n\nOPENCODE_API_KEY=sk-test\nOLLAMA_API_KEY=\nOPENWEBUI_CALLER_KEY=caller\n")
    env = mod.read_env_file(str(env_file))
    assert env == {
        "OPENCODE_API_KEY": "sk-test",
        "OLLAMA_API_KEY": "",
        "OPENWEBUI_CALLER_KEY": "caller",
    }


def test_read_env_file_does_not_print_secrets(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("OPENCODE_API_KEY=sk-super-secret\n")
    mod.read_env_file(str(env_file))
    assert capsys.readouterr().out == ""


def test_reconcile_preserves_non_managed_models(monkeypatch: pytest.MonkeyPatch) -> None:
    now = 1790288638
    non_managed = {
        "id": "user-custom-model",
        "user_id": "admin",
        "base_model_id": "ollama-chat",
        "name": "My Custom Model",
        "params": {},
        "meta": {},
        "access_grants": [],
        "is_active": True,
        "updated_at": now,
        "created_at": now,
    }
    export_rows = [non_managed] + [
        {
            "id": pid,
            "user_id": "admin",
            "base_model_id": "stale",
            "name": "stale",
            "params": {},
            "meta": {},
            "access_grants": [],
            "is_active": True,
            "updated_at": 1,
            "created_at": 1,
        }
        for pid in DEFAULT_MODELS
    ]
    calls: list[tuple[str, str, dict[str, Any] | None]] = []

    def fake_request(
        method: str, url: str, token: str | None = None, payload: dict[str, Any] | None = None
    ) -> tuple[int, Any]:
        calls.append((method, url, payload))
        if method == "GET" and url.endswith("/api/v1/models/export"):
            return 200, export_rows
        if method == "POST" and url.endswith("/api/v1/models/sync"):
            return 200, export_rows
        raise AssertionError(f"unexpected request {method} {url}")

    monkeypatch.setattr(mod, "_request_json_with_retry", fake_request)
    mod.reconcile("http://test", "token", None, MODEL_MAP, DEFAULT_MODELS)
    sync_payload = calls[1][2]
    assert sync_payload is not None
    synced = sync_payload["models"]
    assert non_managed in synced
    assert len(synced) == len(DEFAULT_MODELS) + 1
    preset_ids = [m["id"] for m in synced if m["id"] in DEFAULT_MODELS]
    assert preset_ids == DEFAULT_MODELS
    for model in synced:
        if model["id"] in DEFAULT_MODELS:
            assert model["base_model_id"] == MODEL_MAP[model["id"]]
            assert model["name"] == EXPECTED_NAMES[model["id"]]


def _preset_rows() -> list[dict[str, Any]]:
    return [
        {
            "id": pid,
            "user_id": "admin",
            "base_model_id": alias,
            "name": EXPECTED_NAMES[pid],
            "params": {},
            "meta": {},
            "access_grants": [],
            "is_active": True,
            "updated_at": 1790288638,
            "created_at": 1790288638,
        }
        for pid, alias in MODEL_MAP.items()
    ]


def test_reconcile_falls_back_to_import_on_404(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, str, dict[str, Any] | None]] = []

    def fake_request(
        method: str, url: str, token: str | None = None, payload: dict[str, Any] | None = None
    ) -> tuple[int, Any]:
        calls.append((method, url, payload))
        if method == "GET" and url.endswith("/api/v1/models/export"):
            if len([c for c in calls if c[0] == "GET"]) == 1:
                return 200, []
            return 200, _preset_rows()
        if method == "POST" and url.endswith("/api/v1/models/sync"):
            return 404, {"detail": "not found"}
        if method == "POST" and url.endswith("/api/v1/models/import"):
            return 200, _preset_rows()
        raise AssertionError(f"unexpected request {method} {url}")

    monkeypatch.setattr(mod, "_request_json_with_retry", fake_request)
    mod.reconcile("http://test", "token", None, MODEL_MAP, DEFAULT_MODELS)
    sync_payload = calls[1][2]
    import_payload = calls[2][2]
    assert sync_payload is not None
    assert import_payload == sync_payload
    assert [m["id"] for m in import_payload["models"]] == DEFAULT_MODELS


def test_reconcile_import_fallback_failure_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_request(
        method: str, url: str, token: str | None = None, payload: dict[str, Any] | None = None
    ) -> tuple[int, Any]:
        if method == "GET" and url.endswith("/api/v1/models/export"):
            return 200, []
        if method == "POST" and url.endswith("/api/v1/models/sync"):
            return 405, {"detail": "not allowed"}
        if method == "POST" and url.endswith("/api/v1/models/import"):
            return 422, {"detail": "unprocessable"}
        raise AssertionError(f"unexpected request {method} {url}")

    monkeypatch.setattr(mod, "_request_json_with_retry", fake_request)
    with pytest.raises(RuntimeError, match="import fallback failed"):
        mod.reconcile("http://test", "token", None, MODEL_MAP, DEFAULT_MODELS)


@pytest.mark.parametrize("status", [401, 403, 422])
def test_reconcile_terminal_sync_errors_raise(monkeypatch: pytest.MonkeyPatch, status: int) -> None:
    calls: list[tuple[str, str, dict[str, Any] | None]] = []

    def fake_request(
        method: str, url: str, token: str | None = None, payload: dict[str, Any] | None = None
    ) -> tuple[int, Any]:
        calls.append((method, url, payload))
        if method == "GET" and url.endswith("/api/v1/models/export"):
            return 200, []
        if method == "POST" and url.endswith("/api/v1/models/sync"):
            return status, {"detail": "rejected"}
        raise AssertionError(f"unexpected request {method} {url}")

    monkeypatch.setattr(mod, "_request_json_with_retry", fake_request)
    with pytest.raises(RuntimeError, match="rejected"):
        mod.reconcile("http://test", "token", None, MODEL_MAP, DEFAULT_MODELS)
    assert not [c for c in calls if c[1].endswith("/api/v1/models/import")]


def test_reconcile_sync_200_empty_is_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_request(
        method: str, url: str, token: str | None = None, payload: dict[str, Any] | None = None
    ) -> tuple[int, Any]:
        if method == "GET" and url.endswith("/api/v1/models/export"):
            return 200, []
        if method == "POST" and url.endswith("/api/v1/models/sync"):
            return 200, []
        raise AssertionError(f"unexpected request {method} {url}")

    monkeypatch.setattr(mod, "_request_json_with_retry", fake_request)
    with pytest.raises(RuntimeError, match="empty model list"):
        mod.reconcile("http://test", "token", None, MODEL_MAP, DEFAULT_MODELS)


def test_reconcile_missing_presets_after_sync_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_request(
        method: str, url: str, token: str | None = None, payload: dict[str, Any] | None = None
    ) -> tuple[int, Any]:
        if method == "GET" and url.endswith("/api/v1/models/export"):
            return 200, []
        if method == "POST" and url.endswith("/api/v1/models/sync"):
            return 200, _preset_rows()
        raise AssertionError(f"unexpected request {method} {url}")

    monkeypatch.setattr(mod, "_request_json_with_retry", fake_request)
    with pytest.raises(RuntimeError, match="presets missing after sync"):
        mod.reconcile("http://test", "token", None, MODEL_MAP, DEFAULT_MODELS)


def test_reconcile_first_run_stamps_clock(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(mod.time, "time", lambda: 1790288638)
    calls: list[tuple[str, str, dict[str, Any] | None]] = []

    def fake_request(
        method: str, url: str, token: str | None = None, payload: dict[str, Any] | None = None
    ) -> tuple[int, Any]:
        calls.append((method, url, payload))
        if method == "GET" and url.endswith("/api/v1/models/export"):
            return (200, []) if len([c for c in calls if c[0] == "GET"]) == 1 else (200, _preset_rows())
        if method == "POST" and url.endswith("/api/v1/models/sync"):
            return 200, _preset_rows()
        raise AssertionError(f"unexpected request {method} {url}")

    monkeypatch.setattr(mod, "_request_json_with_retry", fake_request)
    mod.reconcile("http://test", "token", None, MODEL_MAP, DEFAULT_MODELS)
    sync_payload = calls[1][2]
    assert sync_payload is not None
    for model in sync_payload["models"]:
        assert model["updated_at"] == 1790288638
        assert model["created_at"] == 1790288638


def test_to_sync_model_falls_back_to_now_without_usable_timestamps() -> None:
    specs = mod.build_preset_specs(MODEL_MAP, DEFAULT_MODELS)
    for existing in ({}, {"updated_at": None, "created_at": None}, {"updated_at": 0, "created_at": 0}):
        model = mod.to_sync_model(specs[0], "admin", 1790288638, existing)
        assert model["updated_at"] == 1790288638
        assert model["created_at"] == 1790288638


def test_reconcile_second_run_sends_identical_payload_without_server_updated_at(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = iter([1_000_000, 2_000_000])
    monkeypatch.setattr(mod.time, "time", lambda: next(clock))
    server_clock = itertools.count(10_000_000, 10_000_000)
    stored: list[dict[str, Any]] = []
    sync_payloads: list[dict[str, Any]] = []

    def fake_request(
        method: str, url: str, token: str | None = None, payload: dict[str, Any] | None = None
    ) -> tuple[int, Any]:
        if method == "GET" and url.endswith("/api/v1/models/export"):
            return 200, stored
        if method == "POST" and url.endswith("/api/v1/models/sync"):
            assert payload is not None
            sync_payloads.append(payload)
            stored[:] = [{**model, "updated_at": next(server_clock)} for model in payload["models"]]
            return 200, stored
        raise AssertionError(f"unexpected request {method} {url}")

    monkeypatch.setattr(mod, "_request_json_with_retry", fake_request)
    mod.reconcile("http://test", "token", None, MODEL_MAP, DEFAULT_MODELS)
    mod.reconcile("http://test", "token", None, MODEL_MAP, DEFAULT_MODELS)

    assert len(sync_payloads) == 2
    first, second = sync_payloads
    assert [model["updated_at"] for model in first["models"]] == [1_000_000] * len(DEFAULT_MODELS)
    assert [model["updated_at"] for model in second["models"]] == [
        10_000_000 * (index + 1) for index in range(len(DEFAULT_MODELS))
    ]
    assert [model["created_at"] for model in first["models"]] == [1_000_000] * len(DEFAULT_MODELS)
    assert [model["created_at"] for model in second["models"]] == [1_000_000] * len(DEFAULT_MODELS)
    stripped = [
        json.dumps(
            [{k: v for k, v in model.items() if k != "updated_at"} for model in payload["models"]],
            sort_keys=True,
        ).encode()
        for payload in sync_payloads
    ]
    assert stripped[0] == stripped[1]


_COMPOSE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "deploys",
    "openwebui",
    "files",
    "docker-compose.yml",
)

_GROUP_DATA = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "group_data",
)


def _openwebui_group_data(name: str) -> dict[str, Any]:
    with open(os.path.join(_GROUP_DATA, name)) as f:
        tree = ast.parse(f.read())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "openwebui" for target in node.targets
        ):
            data: dict[str, Any] = ast.literal_eval(node.value)
            return data
    raise AssertionError(f"no openwebui assignment in {name}")


def test_group_data_default_models_order() -> None:
    data = _openwebui_group_data("all.py")
    assert data["default_models"] == DEFAULT_MODELS
    assert data["extra_env"]["DEFAULT_MODELS"] == ",".join(DEFAULT_MODELS)


def test_api_keys_enabled_for_open_webui_service() -> None:
    assert _openwebui_group_data("all.py")["extra_env"]["ENABLE_API_KEYS"] == "true"
    with open(_COMPOSE) as f:
        content = f.read()
    block = content[content.index("  open-webui:") : content.index("  aisix:")]
    assert "ENABLE_API_KEYS=${ENABLE_API_KEYS}" in block


def test_compose_enables_session_sharing() -> None:
    with open(_COMPOSE) as f:
        content = f.read()
    assert "DATABASE_ENABLE_SESSION_SHARING=true" in content


_DEPLOY = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "deploys",
    "openwebui",
    "deploy.py",
)


def test_group_data_admin_key_placeholder() -> None:
    with open(os.path.join(_GROUP_DATA, "all.py")) as f:
        content = f.read()
    assert '"openwebui_admin_key": ""' in content


def test_ci_keeps_openwebui_disabled() -> None:
    assert _openwebui_group_data("ci.py")["enabled"] is False


def test_no_caller_split_brain_in_extra_env() -> None:
    with open(os.path.join(_GROUP_DATA, "all.py")) as f:
        content = f.read()
    assert '"openwebui_caller_key": ""' in content
    assert "OPENAI_API_KEYS" not in content


def test_deploy_derives_caller_and_admin_keys() -> None:
    with open(_DEPLOY) as f:
        content = f.read()
    assert "OPENAI_API_KEYS={host.data.openwebui['openwebui_caller_key']}" in content
    assert "OPENWEBUI_API_KEY={host.data.openwebui['openwebui_admin_key']}" in content
    assert "WEBUI_ADMIN_KEY={host.data.openwebui['openwebui_admin_key']}" in content
    assert 'if k != "OPENAI_API_KEYS"' in content


def _render_reconcile_command(compose_project_dir: str) -> str:
    with open(_DEPLOY) as f:
        tree = ast.parse(f.read())
    for node in ast.walk(tree):
        if not isinstance(node, ast.JoinedStr):
            continue
        if not any(
            isinstance(value, ast.FormattedValue)
            and isinstance(value.value, ast.Call)
            and isinstance(value.value.func, ast.Attribute)
            and value.value.func.attr == "quote"
            for value in node.values
        ):
            continue
        code = compile(ast.Expression(body=node), _DEPLOY, "eval")
        globals_dict: dict[str, Any] = {
            "shlex": shlex,
            "sys": types.SimpleNamespace(executable="/usr/bin/python3"),
            "compose_project_dir": compose_project_dir,
        }
        rendered = eval(code, globals_dict)
        assert isinstance(rendered, str)
        return rendered
    raise AssertionError("reconcile command not found in deploy.py")


def test_deploy_reconcile_command_quotes_paths_with_spaces() -> None:
    command = _render_reconcile_command("/home/user/my openwebui")
    assert command == (
        "/usr/bin/python3 '/home/user/my openwebui/update-openwebui-models.py' "
        "--config '/home/user/my openwebui/openwebui-models-config.json' "
        "--env-file '/home/user/my openwebui/.env' "
        "--resources '/home/user/my openwebui/resources.yaml'"
    )


def test_deploy_reconcile_command_plain_paths_unquoted() -> None:
    command = _render_reconcile_command("/home/user/openwebui")
    assert command == (
        "/usr/bin/python3 /home/user/openwebui/update-openwebui-models.py "
        "--config /home/user/openwebui/openwebui-models-config.json "
        "--env-file /home/user/openwebui/.env "
        "--resources /home/user/openwebui/resources.yaml"
    )


def test_authenticate_falls_back_to_env_admin_key(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_request(
        method: str, url: str, token: str | None = None, payload: dict[str, Any] | None = None
    ) -> tuple[int, Any]:
        if url.endswith("/api/v1/auths/signin"):
            return 401, {"detail": "unauthorized"}
        if url.endswith("/api/v1/models/base"):
            assert token == "sk-admin"
            return 200, {"id": "admin"}
        raise AssertionError(f"unexpected request {method} {url}")

    monkeypatch.setattr(mod, "_request_json_with_retry", fake_request)
    token, signin_body = mod.authenticate("http://test", {"OPENWEBUI_API_KEY": "sk-admin"})
    assert token == "sk-admin"
    assert signin_body is None


def test_authenticate_falls_back_to_webui_admin_key(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_request(
        method: str, url: str, token: str | None = None, payload: dict[str, Any] | None = None
    ) -> tuple[int, Any]:
        if url.endswith("/api/v1/auths/signin"):
            return 401, {"detail": "unauthorized"}
        if url.endswith("/api/v1/models/base"):
            assert token == "sk-admin-legacy"
            return 200, {"id": "admin"}
        raise AssertionError(f"unexpected request {method} {url}")

    monkeypatch.setattr(mod, "_request_json_with_retry", fake_request)
    token, _ = mod.authenticate("http://test", {"WEBUI_ADMIN_KEY": "sk-admin-legacy"})
    assert token == "sk-admin-legacy"


def test_authenticate_raises_when_signin_and_admin_key_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def fake_request(
        method: str, url: str, token: str | None = None, payload: dict[str, Any] | None = None
    ) -> tuple[int, Any]:
        calls.append(url)
        if url.endswith("/api/v1/auths/signin"):
            return 401, {"detail": "unauthorized"}
        if url.endswith("/api/v1/models/base"):
            return 403, {"detail": "api key not allowed"}
        raise AssertionError(f"unexpected request {method} {url}")

    monkeypatch.setattr(mod, "_request_json_with_retry", fake_request)
    with pytest.raises(RuntimeError, match="OpenWebUI API key"):
        mod.authenticate("http://test", {"OPENWEBUI_API_KEY": "sk-rejected"})
    assert calls == ["http://test/api/v1/auths/signin", "http://test/api/v1/models/base"]


def test_authenticate_raises_without_admin_key(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_request(
        method: str, url: str, token: str | None = None, payload: dict[str, Any] | None = None
    ) -> tuple[int, Any]:
        if url.endswith("/api/v1/auths/signin"):
            return 401, {"detail": "unauthorized"}
        raise AssertionError(f"unexpected request {method} {url}")

    monkeypatch.setattr(mod, "_request_json_with_retry", fake_request)
    with pytest.raises(RuntimeError, match="OpenWebUI API key"):
        mod.authenticate("http://test", {})


def test_wait_ready_returns_on_200(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def fake_request(
        method: str, url: str, token: str | None = None, payload: dict[str, Any] | None = None
    ) -> tuple[int, Any]:
        calls.append(url)
        return 200, None

    monkeypatch.setattr(mod, "_request_json", fake_request)
    mod.wait_ready("http://test")
    assert calls == ["http://test/ready"]


@pytest.mark.parametrize("error", [URLError("down"), TimeoutError("timed out"), json.JSONDecodeError("x", "", 0)])
def test_wait_ready_retries_until_200(monkeypatch: pytest.MonkeyPatch, error: Exception) -> None:
    calls: list[str] = []

    def fake_request(
        method: str, url: str, token: str | None = None, payload: dict[str, Any] | None = None
    ) -> tuple[int, Any]:
        calls.append(url)
        if len(calls) == 1:
            raise error
        if len(calls) == 2:
            return 503, None
        return 200, None

    monkeypatch.setattr(mod, "_request_json", fake_request)
    monkeypatch.setattr(mod.time, "sleep", lambda seconds: None)
    mod.wait_ready("http://test")
    assert calls == ["http://test/ready", "http://test/ready", "http://test/ready"]


def test_wait_ready_raises_on_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(mod, "READY_TIMEOUT_SECONDS", 0)

    def fake_request(
        method: str, url: str, token: str | None = None, payload: dict[str, Any] | None = None
    ) -> tuple[int, Any]:
        return 503, None

    monkeypatch.setattr(mod, "_request_json", fake_request)
    with pytest.raises(RuntimeError, match="did not become ready"):
        mod.wait_ready("http://test")


def test_request_json_with_retry_returns_success_immediately(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def fake_request(
        method: str, url: str, token: str | None = None, payload: dict[str, Any] | None = None
    ) -> tuple[int, Any]:
        calls.append(url)
        return 200, {"ok": True}

    monkeypatch.setattr(mod, "_request_json", fake_request)
    status, body = mod._request_json_with_retry("GET", "http://test/x")
    assert status == 200
    assert body == {"ok": True}
    assert calls == ["http://test/x"]


def test_request_json_with_retry_retries_on_urlerror(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def fake_request(
        method: str, url: str, token: str | None = None, payload: dict[str, Any] | None = None
    ) -> tuple[int, Any]:
        calls.append(url)
        if len(calls) == 1:
            raise URLError("down")
        return 200, None

    monkeypatch.setattr(mod, "_request_json", fake_request)
    monkeypatch.setattr(mod.time, "sleep", lambda seconds: None)
    status, _ = mod._request_json_with_retry("GET", "http://test/x")
    assert status == 200
    assert len(calls) == 2


def test_request_json_with_retry_retries_on_5xx(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def fake_request(
        method: str, url: str, token: str | None = None, payload: dict[str, Any] | None = None
    ) -> tuple[int, Any]:
        calls.append(url)
        if len(calls) == 1:
            return 503, None
        return 200, None

    monkeypatch.setattr(mod, "_request_json", fake_request)
    monkeypatch.setattr(mod.time, "sleep", lambda seconds: None)
    status, _ = mod._request_json_with_retry("GET", "http://test/x")
    assert status == 200
    assert len(calls) == 2


def test_request_json_with_retry_returns_4xx_immediately(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def fake_request(
        method: str, url: str, token: str | None = None, payload: dict[str, Any] | None = None
    ) -> tuple[int, Any]:
        calls.append(url)
        return 404, {"detail": "not found"}

    monkeypatch.setattr(mod, "_request_json", fake_request)
    status, body = mod._request_json_with_retry("GET", "http://test/x")
    assert status == 404
    assert body == {"detail": "not found"}
    assert len(calls) == 1


def test_request_json_with_retry_passes_token_and_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[tuple[str, str, str | None, dict[str, Any] | None]] = []

    def fake_request(
        method: str, url: str, token: str | None = None, payload: dict[str, Any] | None = None
    ) -> tuple[int, Any]:
        seen.append((method, url, token, payload))
        return 200, None

    monkeypatch.setattr(mod, "_request_json", fake_request)
    mod._request_json_with_retry("POST", "http://test/x", token="sk-test", payload={"a": 1})
    assert seen == [("POST", "http://test/x", "sk-test", {"a": 1})]


def test_request_json_with_retry_raises_after_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(mod, "RETRY_TIMEOUT_SECONDS", 0)

    def fake_request(
        method: str, url: str, token: str | None = None, payload: dict[str, Any] | None = None
    ) -> tuple[int, Any]:
        return 503, None

    monkeypatch.setattr(mod, "_request_json", fake_request)
    with pytest.raises(RuntimeError, match="failed after"):
        mod._request_json_with_retry("GET", "http://test/api")


def test_deploy_reconcile_command_shlex_quoted() -> None:
    with open(_DEPLOY) as f:
        content = f.read()
    reconcile_start = content.index('name="Reconcile openwebui models"')
    assert reconcile_start > content.index("systemd.service(")
    command = content[reconcile_start : content.index("_if=", reconcile_start)]
    assert "shlex.quote" in command
    assert "shlex.quote(sys.executable)" in command
    assert "|| true" not in command
    for interpolation in (
        "{compose_project_dir}/openwebui-models-config.json",
        "{compose_project_dir}/.env",
        "{compose_project_dir}/resources.yaml",
        "{compose_project_dir}/update-openwebui-models.py",
    ):
        assert f"shlex.quote(f'{interpolation}')" in command


def test_deploy_sighup_reloads_aisix() -> None:
    with open(_DEPLOY) as f:
        content = f.read()
    assert "kill -s SIGHUP aisix" in content
    systemd_start = content.index("systemd.service(")
    systemd_end = content.index("server.shell(", systemd_start)
    systemd_block = content[systemd_start:systemd_end]
    assert "aisix_resources_file.changed" not in systemd_block


def test_deploy_copies_reconcile_script() -> None:
    with open(_DEPLOY) as f:
        content = f.read()
    assert "reconcile_script_file = files.put(" in content
    assert "update-openwebui-models.py" in content
    assert 'dest=f"{compose_project_dir}/update-openwebui-models.py"' in content
    reconcile_start = content.index('name="Reconcile openwebui models"')
    command = content[reconcile_start : content.index("_if=", reconcile_start)]
    assert "{compose_project_dir}/update-openwebui-models.py" in command
    assert "../../scripts/update-openwebui-models.py" not in command
    assert "or reconcile_script_file.changed" in content


def test_reconcile_fails_on_base_row_collision(monkeypatch: pytest.MonkeyPatch) -> None:
    base_row = {
        "id": "chat",
        "user_id": "admin",
        "base_model_id": "chat",
        "name": "Chat",
        "params": {},
        "meta": {},
        "access_grants": [],
        "is_active": True,
        "updated_at": 1790288638,
        "created_at": 1790288638,
    }
    calls: list[tuple[str, str, dict[str, Any] | None]] = []

    def fake_request(
        method: str, url: str, token: str | None = None, payload: dict[str, Any] | None = None
    ) -> tuple[int, Any]:
        calls.append((method, url, payload))
        if method == "GET" and url.endswith("/api/v1/models/export"):
            return 200, [base_row]
        raise AssertionError(f"unexpected request {method} {url}")

    monkeypatch.setattr(mod, "_request_json_with_retry", fake_request)
    with pytest.raises(RuntimeError, match="preset id collides with an existing base model row"):
        mod.reconcile("http://test", "token", None, MODEL_MAP, DEFAULT_MODELS)
    assert [c[0] for c in calls] == ["GET"]
    assert not [c for c in calls if c[0] == "POST"]


def test_reconcile_fails_on_base_row_collision_missing_base_model_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base_row = {
        "id": "chat",
        "user_id": "admin",
        "name": "Chat",
        "params": {},
        "meta": {},
        "access_grants": [],
        "is_active": True,
        "updated_at": 1790288638,
        "created_at": 1790288638,
    }
    calls: list[tuple[str, str, dict[str, Any] | None]] = []

    def fake_request(
        method: str, url: str, token: str | None = None, payload: dict[str, Any] | None = None
    ) -> tuple[int, Any]:
        calls.append((method, url, payload))
        if method == "GET" and url.endswith("/api/v1/models/export"):
            return 200, [base_row]
        raise AssertionError(f"unexpected request {method} {url}")

    monkeypatch.setattr(mod, "_request_json_with_retry", fake_request)
    with pytest.raises(RuntimeError, match="preset id collides with an existing base model row"):
        mod.reconcile("http://test", "token", None, MODEL_MAP, DEFAULT_MODELS)
    assert [c[0] for c in calls] == ["GET"]


def test_reconcile_allows_previous_preset_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    previous_preset = {
        "id": "chat",
        "user_id": "admin",
        "base_model_id": "router-chat",
        "name": "Chat",
        "params": {},
        "meta": {},
        "access_grants": [],
        "is_active": True,
        "updated_at": 1790288638,
        "created_at": 1790288638,
    }
    calls: list[tuple[str, str, dict[str, Any] | None]] = []

    def fake_request(
        method: str, url: str, token: str | None = None, payload: dict[str, Any] | None = None
    ) -> tuple[int, Any]:
        calls.append((method, url, payload))
        if method == "GET" and url.endswith("/api/v1/models/export"):
            if len([c for c in calls if c[0] == "GET"]) == 1:
                return 200, [previous_preset]
            return 200, _preset_rows()
        if method == "POST" and url.endswith("/api/v1/models/sync"):
            return 200, _preset_rows()
        raise AssertionError(f"unexpected request {method} {url}")

    monkeypatch.setattr(mod, "_request_json_with_retry", fake_request)
    mod.reconcile("http://test", "token", None, MODEL_MAP, DEFAULT_MODELS)
    sync_payload = calls[1][2]
    assert sync_payload is not None
    assert [m["id"] for m in sync_payload["models"]] == DEFAULT_MODELS
    assert [m["base_model_id"] for m in sync_payload["models"]] == [MODEL_MAP[p] for p in DEFAULT_MODELS]


def _run_main(monkeypatch: pytest.MonkeyPatch, config_path: Path, resources_path: Path) -> None:
    def fake_wait_ready(base_url: str) -> None:
        raise RuntimeError("alias check passed, reached the network")

    monkeypatch.setattr(mod, "wait_ready", fake_wait_ready)
    monkeypatch.setattr(
        sys,
        "argv",
        ["update-openwebui-models.py", "--config", str(config_path), "--resources", str(resources_path)],
    )
    mod.main()


def _write_main_inputs(tmp_path: Path, resources: str) -> tuple[Path, Path]:
    config_path = tmp_path / "openwebui-models-config.json"
    config_path.write_text(json.dumps({"model_map": MODEL_MAP, "default_models": DEFAULT_MODELS}))
    (tmp_path / ".env").write_text("OPENWEBUI_API_KEY=sk-admin\n")
    resources_path = tmp_path / "resources.yaml"
    resources_path.write_text(resources)
    return config_path, resources_path


def test_main_rejects_resources_missing_model_map_alias(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    with open(_RESOURCES) as f:
        real = f.read()
    minimal = real[: real.index("  - display_name: router-linux-cli")] + real[real.index("\napi_keys:") :]
    assert [name for name, _ in mod.parse_aisix_model_names(minimal)] == list(MODEL_MAP.values())[:-1]
    config_path, resources_path = _write_main_inputs(tmp_path, minimal)
    with pytest.raises(RuntimeError, match="router-linux-cli"):
        _run_main(monkeypatch, config_path, resources_path)


def test_main_accepts_extra_router_aliases(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    with open(_RESOURCES) as f:
        real = f.read()
    extra = (
        "  - display_name: router-extra\n"
        "    routing:\n"
        "      strategy: failover\n"
        "      targets:\n"
        "        - model: zen-chat\n"
        "          priority: 100\n"
    )
    spliced = real.replace("\napi_keys:", f"\n{extra}api_keys:")
    assert [name for name, _ in mod.parse_aisix_model_names(spliced)] == list(MODEL_MAP.values()) + ["router-extra"]
    config_path, resources_path = _write_main_inputs(tmp_path, spliced)
    with pytest.raises(RuntimeError, match="reached the network"):
        _run_main(monkeypatch, config_path, resources_path)
