import importlib.util
import json
import os
from email.message import Message
from io import BytesIO
from pathlib import Path
from typing import Any
from unittest import mock
from urllib.error import HTTPError, URLError

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

OPENWEBUI: dict[str, Any] = {
    "default_models": [
        "chat",
        "chat_thinking",
        "web_research",
        "translate_de",
        "translate_en",
        "fix_grammar_en",
        "fix_grammar_de",
        "linux_cli",
    ],
    "model_map": {
        "chat": "router-chat",
        "chat_thinking": "router-chat_thinking",
        "web_research": "router-web_research",
        "translate_de": "router-translate_de",
        "translate_en": "router-translate_en",
        "fix_grammar_en": "router-fix_grammar_en",
        "fix_grammar_de": "router-fix_grammar_de",
        "linux_cli": "router-linux_cli",
    },
}

ROUTER_ALIASES = [
    "router-chat",
    "router-chat_thinking",
    "router-web_research",
    "router-translate_de",
    "router-translate_en",
    "router-fix_grammar_en",
    "router-fix_grammar_de",
    "router-linux_cli",
]

RESOURCES = """\
_format_version: "1"
api_keys:
  - display_name: openwebui
    key_env: OPENWEBUI_CALLER_KEY
    allowed_models:
      - router-chat
      - router-chat_thinking
      - router-web_research
      - router-translate_de
      - router-translate_en
      - router-fix_grammar_en
      - router-fix_grammar_de
      - router-linux_cli
provider_keys:
  - display_name: zen
    provider: openai
    adapter: openai
    api_base: ${ZEN_API_BASE}
    api_key: ${OPENCODE_GO_API_KEY}
  - display_name: ollama
    provider: openai
    adapter: openai
    api_base: ${OLLAMA_API_BASE}
    api_key: ${OLLAMA_API_KEY}
models:
  - display_name: zen-chat
    provider: openai
    model_name: ${ZEN_CHAT_MODEL}
    provider_key: zen
  - display_name: zen-chat_thinking
    provider: openai
    model_name: ${ZEN_CHAT_THINKING_MODEL}
    provider_key: zen
  - display_name: zen-web_research
    provider: openai
    model_name: ${ZEN_WEB_RESEARCH_MODEL}
    provider_key: zen
  - display_name: zen-translate
    provider: openai
    model_name: ${ZEN_TRANSLATE_MODEL}
    provider_key: zen
  - display_name: zen-grammar
    provider: openai
    model_name: ${ZEN_GRAMMAR_MODEL}
    provider_key: zen
  - display_name: zen-linux_cli
    provider: openai
    model_name: ${ZEN_LINUX_CLI_MODEL}
    provider_key: zen
  - display_name: ollama-chat
    provider: openai
    model_name: ${OLLAMA_CHAT_MODEL}
    provider_key: ollama
  - display_name: ollama-chat_thinking
    provider: openai
    model_name: ${OLLAMA_CHAT_THINKING_MODEL}
    provider_key: ollama
  - display_name: ollama-web_research
    provider: openai
    model_name: ${OLLAMA_WEB_RESEARCH_MODEL}
    provider_key: ollama
  - display_name: ollama-translate
    provider: openai
    model_name: ${OLLAMA_TRANSLATE_MODEL}
    provider_key: ollama
  - display_name: ollama-grammar
    provider: openai
    model_name: ${OLLAMA_GRAMMAR_MODEL}
    provider_key: ollama
  - display_name: ollama-linux_cli
    provider: openai
    model_name: ${OLLAMA_LINUX_CLI_MODEL}
    provider_key: ollama
  - display_name: router-chat
    routing:
      strategy: failover
      targets:
        - model: zen-chat
          priority: 100
        - model: ollama-chat
          priority: -1
      retries: 0
      max_fallbacks: 1
      retry_on_429: true
  - display_name: router-chat_thinking
    routing:
      strategy: failover
      targets:
        - model: zen-chat_thinking
          priority: 100
        - model: ollama-chat_thinking
          priority: -1
      retries: 0
      max_fallbacks: 1
      retry_on_429: true
  - display_name: router-web_research
    routing:
      strategy: failover
      targets:
        - model: zen-web_research
          priority: 100
        - model: ollama-web_research
          priority: -1
      retries: 0
      max_fallbacks: 1
      retry_on_429: true
  - display_name: router-translate_de
    routing:
      strategy: failover
      targets:
        - model: zen-translate
          priority: 100
        - model: ollama-translate
          priority: -1
      retries: 0
      max_fallbacks: 1
      retry_on_429: true
  - display_name: router-translate_en
    routing:
      strategy: failover
      targets:
        - model: zen-translate
          priority: 100
        - model: ollama-translate
          priority: -1
      retries: 0
      max_fallbacks: 1
      retry_on_429: true
  - display_name: router-fix_grammar_en
    routing:
      strategy: failover
      targets:
        - model: zen-grammar
          priority: 100
        - model: ollama-grammar
          priority: -1
      retries: 0
      max_fallbacks: 1
      retry_on_429: true
  - display_name: router-fix_grammar_de
    routing:
      strategy: failover
      targets:
        - model: zen-grammar
          priority: 100
        - model: ollama-grammar
          priority: -1
      retries: 0
      max_fallbacks: 1
      retry_on_429: true
  - display_name: router-linux_cli
    routing:
      strategy: failover
      targets:
        - model: zen-linux_cli
          priority: 100
        - model: ollama-linux_cli
          priority: -1
      retries: 0
      max_fallbacks: 1
      retry_on_429: true
"""


def _write(tmp_path: Path, content: str) -> str:
    path = tmp_path / "aisix-resources.yaml"
    path.write_text(content)
    return str(path)


def _http_error(code: int) -> HTTPError:
    return HTTPError("http://x", code, "err", Message(), BytesIO(b'{"detail": "x"}'))


class _FakeResponse:
    def __init__(self, status: int, body: bytes) -> None:
        self.status = status
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *args: Any) -> None:
        return None


def _fake_urlopen(responses: list[Any]) -> Any:
    def fake_urlopen(req: Any, timeout: int = 30) -> Any:
        resp = responses.pop(0)
        if isinstance(resp, HTTPError):
            raise resp
        if isinstance(resp, URLError):
            raise resp
        status, body = resp
        return _FakeResponse(status, body)

    return fake_urlopen


def test_build_preset_specs_eight_in_order() -> None:
    specs = mod.build_preset_specs(OPENWEBUI)
    assert [s["id"] for s in specs] == OPENWEBUI["default_models"]
    assert [s["base_model_id"] for s in specs] == ROUTER_ALIASES
    assert specs[0]["name"] == "Chat"
    assert specs[1]["name"] == "Chat (Thinking)"
    assert specs[2]["name"] == "Web Research"
    assert specs[2]["web_search"] is True
    assert specs[0]["web_search"] is False


def test_build_preset_specs_id_collision_raises() -> None:
    openwebui = {"default_models": ["chat"], "model_map": {"chat": "chat"}}
    with pytest.raises(ValueError, match="collides"):
        mod.build_preset_specs(openwebui)


def test_parse_aisix_model_names_valid(tmp_path: Path) -> None:
    assert mod.parse_aisix_model_names(_write(tmp_path, RESOURCES)) == ROUTER_ALIASES


def test_parse_aisix_model_names_rejects_tabs(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="tabs"):
        mod.parse_aisix_model_names(_write(tmp_path, '_format_version: "1"\nmodels:\n\t- display_name: router-chat\n'))


def test_parse_aisix_model_names_rejects_anchors(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="anchors"):
        mod.parse_aisix_model_names(
            _write(tmp_path, '_format_version: "1"\nmodels:\n  - display_name: &anchor router-chat\n')
        )


def test_parse_aisix_model_names_rejects_flow_style(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="flow style"):
        mod.parse_aisix_model_names(_write(tmp_path, '_format_version: "1"\nmodels: []\n'))


def test_parse_aisix_model_names_rejects_duplicate_keys(tmp_path: Path) -> None:
    content = '_format_version: "1"\nmodels:\n  - display_name: router-chat\nmodels:\n  - display_name: router-chat\n'
    with pytest.raises(ValueError, match="duplicate key"):
        mod.parse_aisix_model_names(_write(tmp_path, content))


def test_parse_aisix_model_names_rejects_missing_format_version(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="_format_version"):
        mod.parse_aisix_model_names(_write(tmp_path, "models:\n  - display_name: router-chat\n"))


def test_to_sync_model_full_envelope() -> None:
    spec = mod.build_preset_specs(OPENWEBUI)[0]
    model = mod.to_sync_model(spec, "owner-id", {})
    assert set(model) == {
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
    }
    assert model["id"] == "chat"
    assert model["user_id"] == "owner-id"
    assert model["base_model_id"] == "router-chat"
    assert model["name"] == "Chat"
    assert model["params"]["system"] == spec["system"]
    assert model["access_grants"] == []
    assert model["is_active"] is True
    assert isinstance(model["updated_at"], int)
    assert isinstance(model["created_at"], int)
    assert "system" not in model["meta"]
    assert model["meta"]["capabilities"]["chat"] is True
    assert model["meta"]["capabilities"]["web_search"] is False
    assert model["meta"]["capabilities"]["vision"] is False
    assert "defaultFeatureIds" not in model["meta"]
    assert "builtinTools" not in model["meta"]
    assert "function_calling" not in model["params"]


def test_to_sync_model_web_research_capabilities() -> None:
    spec = mod.build_preset_specs(OPENWEBUI)[2]
    assert spec["id"] == "web_research"
    model = mod.to_sync_model(spec, "owner-id", {})
    assert model["meta"]["capabilities"]["web_search"] is True
    assert model["meta"]["defaultFeatureIds"] == ["web_search"]
    assert model["meta"]["builtinTools"] == {"web_search": True}
    assert model["params"]["function_calling"] == "native"
    assert model["meta"]["capabilities"]["vision"] is False
    assert model["meta"]["capabilities"]["code_interpreter"] is False
    assert "system" not in model["meta"]


def test_to_sync_model_preserves_existing_timestamps() -> None:
    spec = mod.build_preset_specs(OPENWEBUI)[0]
    existing = {"chat": {"updated_at": 111, "created_at": 222}}
    model = mod.to_sync_model(spec, "owner-id", existing)
    assert model["updated_at"] == 111
    assert model["created_at"] == 222


def test_to_sync_model_coerces_existing_timestamps_to_int() -> None:
    spec = mod.build_preset_specs(OPENWEBUI)[0]
    existing = {"chat": {"updated_at": "111", "created_at": "222"}}
    model = mod.to_sync_model(spec, "owner-id", existing)
    assert model["updated_at"] == 111
    assert model["created_at"] == 222


def test_read_env_file_parses(tmp_path: Path) -> None:
    path = tmp_path / ".env"
    path.write_text("# comment\nKEY=value\nEMPTY=\n")
    assert mod.read_env_file(str(path)) == {"KEY": "value", "EMPTY": ""}


def test_read_env_file_error_does_not_expose_value(tmp_path: Path) -> None:
    path = tmp_path / ".env"
    path.write_text("SECRET=super-secret-value\nMALFORMED\n")
    with pytest.raises(ValueError) as excinfo:
        mod.read_env_file(str(path))
    assert "super-secret-value" not in str(excinfo.value)


def test_reconcile_exact_sync_body() -> None:
    specs = mod.build_preset_specs(OPENWEBUI)
    existing = [
        {"id": "chat", "base_model_id": "router-chat", "updated_at": 1, "created_at": 2},
        {
            "id": "unrelated",
            "user_id": "owner",
            "base_model_id": None,
            "name": "Unrelated",
            "params": {},
            "meta": {},
            "access_grants": [],
            "is_active": True,
            "updated_at": 3,
            "created_at": 4,
        },
    ]
    captured: dict[str, Any] = {}
    get_count = 0

    def fake_request_json(
        method: str,
        url: str,
        token: str | None = None,
        payload: dict[str, Any] | None = None,
        retries: int = 5,
    ) -> tuple[int, Any]:
        nonlocal get_count
        if method == "GET" and url.endswith("/api/v1/models"):
            get_count += 1
            if get_count == 1:
                return 200, existing
            return 200, captured["payload"]["models"]
        if method == "POST" and url.endswith("/api/v1/models/sync"):
            assert payload is not None
            captured["payload"] = payload
            return 200, payload["models"]
        raise AssertionError(f"unexpected call {method} {url}")

    with mock.patch.object(mod, "request_json", side_effect=fake_request_json):
        mod.reconcile("http://x", "token", "owner", specs)

    body = captured["payload"]
    assert set(body) == {"models"}
    assert len(body["models"]) == 9
    ids = [m["id"] for m in body["models"]]
    assert ids[:8] == OPENWEBUI["default_models"]
    assert ids[8] == "unrelated"
    chat = body["models"][0]
    assert chat["base_model_id"] == "router-chat"
    assert chat["user_id"] == "owner"
    assert chat["updated_at"] == 1
    assert chat["created_at"] == 2
    preserved = body["models"][8]
    assert set(preserved) == {
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
    }
    assert preserved["id"] == "unrelated"
    assert preserved["user_id"] == "owner"
    assert preserved["updated_at"] == 3
    assert preserved["created_at"] == 4


def test_reconcile_preserved_rows_normalized_into_full_envelopes() -> None:
    specs = mod.build_preset_specs(OPENWEBUI)
    existing = [
        {"id": "chat", "base_model_id": "router-chat", "updated_at": 1, "created_at": 2},
        {"id": "custom", "base_model_id": "some-base", "name": "Custom", "updated_at": "5", "created_at": "6"},
    ]
    captured: dict[str, Any] = {}
    get_count = 0

    def fake_request_json(
        method: str,
        url: str,
        token: str | None = None,
        payload: dict[str, Any] | None = None,
        retries: int = 5,
    ) -> tuple[int, Any]:
        nonlocal get_count
        if method == "GET" and url.endswith("/api/v1/models"):
            get_count += 1
            if get_count == 1:
                return 200, existing
            return 200, captured["payload"]["models"]
        if method == "POST" and url.endswith("/api/v1/models/sync"):
            assert payload is not None
            captured["payload"] = payload
            return 200, payload["models"]
        raise AssertionError(f"unexpected call {method} {url}")

    with mock.patch.object(mod, "request_json", side_effect=fake_request_json):
        mod.reconcile("http://x", "token", "owner", specs)

    preserved = [m for m in captured["payload"]["models"] if m["id"] == "custom"][0]
    assert set(preserved) == {
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
    }
    assert preserved["id"] == "custom"
    assert preserved["user_id"] == "owner"
    assert preserved["base_model_id"] == "some-base"
    assert preserved["name"] == "Custom"
    assert preserved["params"] == {}
    assert preserved["meta"] == {}
    assert preserved["access_grants"] == []
    assert preserved["is_active"] is True
    assert preserved["updated_at"] == 5
    assert preserved["created_at"] == 6


def test_reconcile_preserved_rows_normalized_from_info_envelope() -> None:
    specs = mod.build_preset_specs(OPENWEBUI)
    existing = [
        {"id": "chat", "base_model_id": "router-chat", "updated_at": 1, "created_at": 2},
        {
            "id": "custom",
            "name": "Custom",
            "info": {
                "id": "custom",
                "user_id": "other-owner",
                "base_model_id": "some-base",
                "name": "Custom",
                "params": {"system": "x"},
                "meta": {"capabilities": {"chat": True}},
                "access_grants": ["grant-1"],
                "is_active": False,
                "updated_at": "7",
                "created_at": "8",
            },
        },
    ]
    captured: dict[str, Any] = {}
    get_count = 0

    def fake_request_json(
        method: str,
        url: str,
        token: str | None = None,
        payload: dict[str, Any] | None = None,
        retries: int = 5,
    ) -> tuple[int, Any]:
        nonlocal get_count
        if method == "GET" and url.endswith("/api/v1/models"):
            get_count += 1
            if get_count == 1:
                return 200, existing
            return 200, captured["payload"]["models"]
        if method == "POST" and url.endswith("/api/v1/models/sync"):
            assert payload is not None
            captured["payload"] = payload
            return 200, payload["models"]
        raise AssertionError(f"unexpected call {method} {url}")

    with mock.patch.object(mod, "request_json", side_effect=fake_request_json):
        mod.reconcile("http://x", "token", "owner", specs)

    preserved = [m for m in captured["payload"]["models"] if m["id"] == "custom"][0]
    assert preserved["user_id"] == "other-owner"
    assert preserved["base_model_id"] == "some-base"
    assert preserved["name"] == "Custom"
    assert preserved["params"] == {"system": "x"}
    assert preserved["meta"] == {"capabilities": {"chat": True}}
    assert preserved["access_grants"] == ["grant-1"]
    assert preserved["is_active"] is False
    assert preserved["updated_at"] == 7
    assert preserved["created_at"] == 8


def test_reconcile_verifies_base_model_id_from_info() -> None:
    specs = mod.build_preset_specs(OPENWEBUI)
    existing = [
        {"id": "chat", "base_model_id": "router-chat", "updated_at": 1, "created_at": 2},
        {"id": "unrelated", "base_model_id": None, "updated_at": 3, "created_at": 4},
    ]
    get_count = 0

    def fake_request_json(
        method: str,
        url: str,
        token: str | None = None,
        payload: dict[str, Any] | None = None,
        retries: int = 5,
    ) -> tuple[int, Any]:
        nonlocal get_count
        if method == "GET" and url.endswith("/api/v1/models"):
            get_count += 1
            if get_count == 1:
                return 200, existing
            return 200, [
                {"id": s["id"], "name": s["name"], "info": {"base_model_id": s["base_model_id"]}} for s in specs
            ]
        if method == "POST" and url.endswith("/api/v1/models/sync"):
            assert payload is not None
            return 200, payload["models"]
        raise AssertionError(f"unexpected call {method} {url}")

    with mock.patch.object(mod, "request_json", side_effect=fake_request_json):
        mod.reconcile("http://x", "token", "owner", specs)


def test_reconcile_id_collision_fails_before_sync() -> None:
    specs = mod.build_preset_specs(OPENWEBUI)
    existing = [{"id": "chat", "base_model_id": "router-other", "updated_at": "t1", "created_at": "t2"}]

    def fake_request_json(
        method: str,
        url: str,
        token: str | None = None,
        payload: dict[str, Any] | None = None,
        retries: int = 5,
    ) -> tuple[int, Any]:
        if method == "GET" and url.endswith("/api/v1/models"):
            return 200, existing
        raise AssertionError(f"unexpected call {method} {url}")

    with mock.patch.object(mod, "request_json", side_effect=fake_request_json):
        with pytest.raises(RuntimeError, match="base_model_id"):
            mod.reconcile("http://x", "token", "owner", specs)


def test_reconcile_sync_200_empty_is_success() -> None:
    specs = mod.build_preset_specs(OPENWEBUI)
    get_count = 0

    def fake_request_json(
        method: str,
        url: str,
        token: str | None = None,
        payload: dict[str, Any] | None = None,
        retries: int = 5,
    ) -> tuple[int, Any]:
        nonlocal get_count
        if method == "GET" and url.endswith("/api/v1/models"):
            get_count += 1
            if get_count == 1:
                return 200, []
            return 200, [{"id": s["id"], "info": {"base_model_id": s["base_model_id"]}} for s in specs]
        if method == "POST" and url.endswith("/api/v1/models/sync"):
            return 200, []
        raise AssertionError(f"unexpected call {method} {url}")

    with mock.patch.object(mod, "request_json", side_effect=fake_request_json):
        mod.reconcile("http://x", "token", "owner", specs)


def test_reconcile_sync_non_200_is_failure() -> None:
    specs = mod.build_preset_specs(OPENWEBUI)

    def fake_request_json(
        method: str,
        url: str,
        token: str | None = None,
        payload: dict[str, Any] | None = None,
        retries: int = 5,
    ) -> tuple[int, Any]:
        if method == "GET" and url.endswith("/api/v1/models"):
            return 200, []
        if method == "POST" and url.endswith("/api/v1/models/sync"):
            return 500, {"detail": "boom"}
        raise AssertionError(f"unexpected call {method} {url}")

    with mock.patch.object(mod, "request_json", side_effect=fake_request_json):
        with pytest.raises(RuntimeError, match="sync failed"):
            mod.reconcile("http://x", "token", "owner", specs)


def test_reconcile_import_fallback_on_404() -> None:
    specs = mod.build_preset_specs(OPENWEBUI)
    calls: list[tuple[str, str]] = []
    import_payloads: list[dict[str, Any]] = []

    def fake_request_json(
        method: str,
        url: str,
        token: str | None = None,
        payload: dict[str, Any] | None = None,
        retries: int = 5,
    ) -> tuple[int, Any]:
        calls.append((method, url))
        if method == "GET" and url.endswith("/api/v1/models"):
            if calls.count(("GET", url)) == 1:
                return 200, []
            return 200, [{"id": s["id"], "base_model_id": s["base_model_id"]} for s in specs]
        if method == "POST" and url.endswith("/api/v1/models/sync"):
            return 404, {"detail": "not found"}
        if method == "POST" and url.endswith("/api/v1/models/import"):
            assert payload is not None
            import_payloads.append(payload)
            return 200, True
        raise AssertionError(f"unexpected call {method} {url}")

    with mock.patch.object(mod, "request_json", side_effect=fake_request_json):
        mod.reconcile("http://x", "token", "owner", specs)

    import_calls = [c for c in calls if c[0] == "POST" and c[1].endswith("/api/v1/models/import")]
    assert len(import_calls) == 1
    assert set(import_payloads[0]) == {"models"}
    assert [m["id"] for m in import_payloads[0]["models"]] == OPENWEBUI["default_models"]
    assert all(isinstance(m["updated_at"], int) for m in import_payloads[0]["models"])
    assert all(isinstance(m["created_at"], int) for m in import_payloads[0]["models"])


def test_reconcile_import_fallback_raises_on_error() -> None:
    specs = mod.build_preset_specs(OPENWEBUI)

    def fake_request_json(
        method: str,
        url: str,
        token: str | None = None,
        payload: dict[str, Any] | None = None,
        retries: int = 5,
    ) -> tuple[int, Any]:
        if method == "GET" and url.endswith("/api/v1/models"):
            return 200, []
        if method == "POST" and url.endswith("/api/v1/models/sync"):
            return 405, {"detail": "method not allowed"}
        if method == "POST" and url.endswith("/api/v1/models/import"):
            return 500, {"detail": "boom"}
        raise AssertionError(f"unexpected call {method} {url}")

    with mock.patch.object(mod, "request_json", side_effect=fake_request_json):
        with pytest.raises(RuntimeError, match="import failed"):
            mod.reconcile("http://x", "token", "owner", specs)


def test_reconcile_422_is_terminal() -> None:
    specs = mod.build_preset_specs(OPENWEBUI)

    def fake_request_json(
        method: str,
        url: str,
        token: str | None = None,
        payload: dict[str, Any] | None = None,
        retries: int = 5,
    ) -> tuple[int, Any]:
        if method == "GET" and url.endswith("/api/v1/models"):
            return 200, []
        if method == "POST" and url.endswith("/api/v1/models/sync"):
            return 422, {"detail": "invalid"}
        raise AssertionError(f"unexpected call {method} {url}")

    with mock.patch.object(mod, "request_json", side_effect=fake_request_json):
        with pytest.raises(RuntimeError, match="sync failed"):
            mod.reconcile("http://x", "token", "owner", specs)


def test_reconcile_idempotent() -> None:
    specs = mod.build_preset_specs(OPENWEBUI)
    existing = [
        {"id": "chat", "base_model_id": "router-chat", "updated_at": 1, "created_at": 2},
        {"id": "unrelated", "base_model_id": None, "updated_at": 3, "created_at": 4},
    ]
    payloads: list[dict[str, Any]] = []

    def fake_request_json(
        method: str,
        url: str,
        token: str | None = None,
        payload: dict[str, Any] | None = None,
        retries: int = 5,
    ) -> tuple[int, Any]:
        if method == "GET" and url.endswith("/api/v1/models"):
            if payloads:
                return 200, payloads[-1]["models"]
            return 200, existing
        if method == "POST" and url.endswith("/api/v1/models/sync"):
            assert payload is not None
            payloads.append(payload)
            return 200, payload["models"]
        raise AssertionError(f"unexpected call {method} {url}")

    with mock.patch.object(mod, "request_json", side_effect=fake_request_json):
        mod.reconcile("http://x", "token", "owner", specs)
        mod.reconcile("http://x", "token", "owner", specs)

    assert payloads[0] == payloads[1]


def test_authenticate_with_admin_key() -> None:
    def fake_request_json(
        method: str,
        url: str,
        token: str | None = None,
        payload: dict[str, Any] | None = None,
        retries: int = 5,
    ) -> tuple[int, Any]:
        assert token == "sk-admin"
        assert url.endswith("/api/v1/users/user")
        return 200, {"id": "owner-id"}

    with mock.patch.object(mod, "request_json", side_effect=fake_request_json):
        token, owner = mod.authenticate("http://x", {"OPENWEBUI_ADMIN_API_KEY": "sk-admin"})
    assert token == "sk-admin"
    assert owner == "owner-id"


def test_authenticate_signin_without_admin_key() -> None:
    def fake_request_json(
        method: str,
        url: str,
        token: str | None = None,
        payload: dict[str, Any] | None = None,
        retries: int = 5,
    ) -> tuple[int, Any]:
        assert method == "POST"
        assert url.endswith("/api/v1/auths/signin")
        assert payload == {"email": "", "password": ""}
        return 200, {"token": "jwt", "id": "owner-id"}

    with mock.patch.object(mod, "request_json", side_effect=fake_request_json):
        token, owner = mod.authenticate("http://x", {})
    assert token == "jwt"
    assert owner == "owner-id"


def test_authenticate_terminal_error() -> None:
    def fake_request_json(
        method: str,
        url: str,
        token: str | None = None,
        payload: dict[str, Any] | None = None,
        retries: int = 5,
    ) -> tuple[int, Any]:
        return 401, {"detail": "unauthorized"}

    with mock.patch.object(mod, "request_json", side_effect=fake_request_json):
        with pytest.raises(RuntimeError, match="OPENWEBUI_ADMIN_API_KEY"):
            mod.authenticate("http://x", {})


def test_request_json_retries_on_503_then_succeeds() -> None:
    responses: list[Any] = [_http_error(503), _http_error(503), (200, b'{"ok": true}')]
    with mock.patch.object(mod, "urlopen", side_effect=_fake_urlopen(responses)), mock.patch.object(mod.time, "sleep"):
        status, data = mod.request_json("GET", "http://x")
    assert status == 200
    assert data == {"ok": True}


def test_request_json_retries_on_429_then_succeeds() -> None:
    responses: list[Any] = [_http_error(429), (200, b"{}")]
    with mock.patch.object(mod, "urlopen", side_effect=_fake_urlopen(responses)), mock.patch.object(mod.time, "sleep"):
        status, data = mod.request_json("GET", "http://x")
    assert status == 200
    assert data == {}


def test_request_json_retries_on_urlerror_then_succeeds() -> None:
    responses: list[Any] = [URLError("boom"), (200, b"[]")]
    with mock.patch.object(mod, "urlopen", side_effect=_fake_urlopen(responses)), mock.patch.object(mod.time, "sleep"):
        status, data = mod.request_json("GET", "http://x")
    assert status == 200
    assert data == []


def test_request_json_returns_http_error_body() -> None:
    responses: list[Any] = [_http_error(422)]
    with mock.patch.object(mod, "urlopen", side_effect=_fake_urlopen(responses)):
        status, data = mod.request_json("GET", "http://x")
    assert status == 422
    assert data == {"detail": "x"}


def test_load_config(tmp_path: Path) -> None:
    models_path = tmp_path / "openwebui-models.json"
    models_path.write_text(json.dumps(OPENWEBUI))
    openwebui, aliases = mod.load_config(str(models_path), _write(tmp_path, RESOURCES))
    assert openwebui["default_models"] == OPENWEBUI["default_models"]
    assert aliases == ROUTER_ALIASES
