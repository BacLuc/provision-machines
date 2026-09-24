import importlib.util
import io
import json
import os
import urllib.error
from email.message import Message
from pathlib import Path
from typing import Any
from urllib.request import Request

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

RENDERED_CONFIG = """\
model_list:
  - model_name: router-chat
    litellm_params:
      model: openai/deepseek-v4-flash
      api_base: os.environ/ZEN_API_BASE
      api_key: os.environ/OPENCODE_GO_API_KEY
  - model_name: router-ollama
    litellm_params:
      model: ollama_chat/qwen2.5:3b
      api_base: os.environ/OLLAMA_API_BASE
router_settings:
  fallbacks:
    - router-chat: [router-ollama]
"""


class _FakeResponse:
    def __init__(self, status: int, body: bytes) -> None:
        self.status = status
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None


def _chat_spec() -> dict[str, Any]:
    return {
        "id": "chat",
        "name": "Chat",
        "system": "You are a helpful assistant.",
        "web_search": False,
        "base_model_id": "router-chat",
    }


def _web_research_spec() -> dict[str, Any]:
    return {
        "id": "web_research",
        "name": "Web Research",
        "system": "You are a web research assistant.",
        "web_search": True,
        "base_model_id": "router-web-research",
    }


def test_presets_cover_eight_fixed_ids() -> None:
    assert list(mod.PRESETS) == [
        "chat",
        "chat_thinking",
        "web_research",
        "translate_de",
        "translate_en",
        "fix_grammar_en",
        "fix_grammar_de",
        "linux_cli",
    ]


def test_build_preset_specs_maps_base_model_id() -> None:
    openwebui = {
        "default_models": ["chat", "web_research"],
        "model_map": {"chat": "router-chat", "web_research": "router-web-research"},
    }
    specs = mod.build_preset_specs(openwebui, ["router-chat", "router-web-research"])
    assert [s["id"] for s in specs] == ["chat", "web_research"]
    assert [s["base_model_id"] for s in specs] == ["router-chat", "router-web-research"]


def test_build_preset_specs_raises_on_id_collision() -> None:
    openwebui = {
        "default_models": ["chat"],
        "model_map": {"chat": "chat"},
    }
    with pytest.raises(ValueError, match="differ"):
        mod.build_preset_specs(openwebui, ["chat"])


def test_build_preset_specs_raises_on_unknown_router_model() -> None:
    openwebui = {
        "default_models": ["chat"],
        "model_map": {"chat": "router-chat"},
    }
    with pytest.raises(ValueError, match="not in the router config"):
        mod.build_preset_specs(openwebui, ["router-other"])


def test_build_preset_specs_raises_on_unknown_preset() -> None:
    openwebui = {
        "default_models": ["nope"],
        "model_map": {"nope": "router-nope"},
    }
    with pytest.raises(ValueError, match="Unknown preset"):
        mod.build_preset_specs(openwebui, ["router-nope"])


def test_to_sync_model_full_envelope() -> None:
    model = mod.to_sync_model(_chat_spec(), "owner-id", None)
    assert model["id"] == "chat"
    assert model["user_id"] == "owner-id"
    assert model["base_model_id"] == "router-chat"
    assert model["name"] == "Chat"
    assert model["params"]["system"] == "You are a helpful assistant."
    assert model["access_grants"] == []
    assert model["is_active"] is True
    assert "updated_at" in model
    assert "created_at" in model


def test_to_sync_model_web_research_tools() -> None:
    model = mod.to_sync_model(_web_research_spec(), "owner", None)
    assert model["meta"]["capabilities"]["web_search"] is True
    assert model["meta"]["defaultFeatureIds"] == ["web_search"]
    assert model["meta"]["builtinTools"] == {"web_search": True}
    assert model["params"]["function_calling"] == "native"


def test_to_sync_model_non_web_research_has_no_tools() -> None:
    model = mod.to_sync_model(_chat_spec(), "owner", None)
    assert model["meta"]["capabilities"]["web_search"] is False
    assert "defaultFeatureIds" not in model["meta"]
    assert "builtinTools" not in model["meta"]
    assert "function_calling" not in model["params"]


def test_parse_litellm_model_names_valid(tmp_path: Path) -> None:
    p = tmp_path / "litellm-config.yaml"
    p.write_text(RENDERED_CONFIG)
    assert mod.parse_litellm_model_names(str(p)) == ["router-chat", "router-ollama"]


def test_parse_litellm_model_names_rejects_tabs(tmp_path: Path) -> None:
    p = tmp_path / "litellm-config.yaml"
    p.write_text("model_list:\n\t- model_name: router-chat\n")
    with pytest.raises(ValueError, match="Tabs"):
        mod.parse_litellm_model_names(str(p))


def test_parse_litellm_model_names_rejects_flow(tmp_path: Path) -> None:
    p = tmp_path / "litellm-config.yaml"
    p.write_text("model_list:\n  - model_name: [router-chat]\n")
    with pytest.raises(ValueError, match="Invalid model_name"):
        mod.parse_litellm_model_names(str(p))


def test_parse_litellm_model_names_rejects_duplicates(tmp_path: Path) -> None:
    p = tmp_path / "litellm-config.yaml"
    p.write_text("model_list:\n  - model_name: router-chat\n  - model_name: router-chat\n")
    with pytest.raises(ValueError, match="Duplicate"):
        mod.parse_litellm_model_names(str(p))


def test_parse_litellm_model_names_rejects_malformed(tmp_path: Path) -> None:
    p = tmp_path / "litellm-config.yaml"
    p.write_text("model_list:\n  - model_name: router chat\n")
    with pytest.raises(ValueError, match="Invalid model_name"):
        mod.parse_litellm_model_names(str(p))


def test_read_env_file_parses_values(tmp_path: Path) -> None:
    p = tmp_path / ".env"
    p.write_text("LITELLM_MASTER_KEY=sk-secret\nOPENWEBUI_ADMIN_API_KEY=\nZEN_API_BASE=https://example.com\n")
    env = mod.read_env_file(str(p))
    assert env["LITELLM_MASTER_KEY"] == "sk-secret"
    assert env["OPENWEBUI_ADMIN_API_KEY"] == ""
    assert env["ZEN_API_BASE"] == "https://example.com"


def test_read_env_file_never_prints_secrets(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    p = tmp_path / ".env"
    p.write_text("LITELLM_MASTER_KEY=sk-super-secret\n")
    mod.read_env_file(str(p))
    captured = capsys.readouterr()
    assert "sk-super-secret" not in captured.out
    assert "sk-super-secret" not in captured.err


def test_reconcile_sends_exact_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, str, dict[str, Any] | None]] = []
    state: dict[str, Any] = {}

    def fake_request(
        method: str,
        url: str,
        token: str | None = None,
        payload: dict[str, Any] | None = None,
        timeout: int = 30,
        retries: int = 3,
        _calls: list[tuple[str, str, dict[str, Any] | None]] = calls,
        _state: dict[str, Any] = state,
    ) -> tuple[int, object]:
        _calls.append((method, url, payload))
        if url.endswith("/api/v1/models/export"):
            return 200, _state.get("synced", [])
        if url.endswith("/api/v1/models/sync"):
            synced = payload["models"] if payload else []
            _state["synced"] = synced
            return 200, synced
        raise AssertionError(f"unexpected url {url}")

    monkeypatch.setattr(mod, "request_json", fake_request)
    mod.reconcile("http://x", "token", "owner", [_chat_spec()], [])
    sync_call = next(c for c in calls if c[0] == "POST" and c[1].endswith("/api/v1/models/sync"))
    payload = sync_call[2]
    assert payload is not None
    assert list(payload.keys()) == ["models"]
    assert [m["id"] for m in payload["models"]] == ["chat"]
    assert payload["models"][0]["base_model_id"] == "router-chat"


def test_reconcile_preserves_unrelated_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, str, dict[str, Any] | None]] = []
    state: dict[str, Any] = {}
    unrelated = {
        "id": "other",
        "user_id": "u",
        "base_model_id": "x",
        "name": "Other",
        "params": {},
        "meta": {},
        "access_grants": [],
        "is_active": True,
        "updated_at": "t",
        "created_at": "t",
    }

    def fake_request(
        method: str,
        url: str,
        token: str | None = None,
        payload: dict[str, Any] | None = None,
        timeout: int = 30,
        retries: int = 3,
        _calls: list[tuple[str, str, dict[str, Any] | None]] = calls,
        _state: dict[str, Any] = state,
    ) -> tuple[int, object]:
        _calls.append((method, url, payload))
        if url.endswith("/api/v1/models/export"):
            return 200, _state.get("synced", [unrelated])
        if url.endswith("/api/v1/models/sync"):
            synced = payload["models"] if payload else []
            _state["synced"] = synced
            return 200, synced
        raise AssertionError(f"unexpected url {url}")

    monkeypatch.setattr(mod, "request_json", fake_request)
    mod.reconcile("http://x", "token", "owner", [_chat_spec()], [unrelated])
    sync_call = next(c for c in calls if c[0] == "POST" and c[1].endswith("/api/v1/models/sync"))
    payload = sync_call[2]
    assert payload is not None
    assert [m["id"] for m in payload["models"]] == ["chat", "other"]


def test_reconcile_preserves_timestamps_from_export(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, str, dict[str, Any] | None]] = []
    state: dict[str, Any] = {}

    def fake_request(
        method: str,
        url: str,
        token: str | None = None,
        payload: dict[str, Any] | None = None,
        timeout: int = 30,
        retries: int = 3,
        _calls: list[tuple[str, str, dict[str, Any] | None]] = calls,
        _state: dict[str, Any] = state,
    ) -> tuple[int, object]:
        _calls.append((method, url, payload))
        if url.endswith("/api/v1/models/export"):
            return 200, _state.get("synced", [])
        if url.endswith("/api/v1/models/sync"):
            synced = payload["models"] if payload else []
            _state["synced"] = synced
            return 200, synced
        raise AssertionError(f"unexpected url {url}")

    monkeypatch.setattr(mod, "request_json", fake_request)
    existing = [
        {
            "id": "chat",
            "user_id": "u",
            "base_model_id": "router-chat",
            "name": "Chat",
            "params": {"system": "s"},
            "meta": {},
            "access_grants": [],
            "is_active": True,
            "updated_at": 1767225600,
            "created_at": 1767225600,
        }
    ]
    mod.reconcile("http://x", "token", "owner", [_chat_spec()], existing)
    sync_call = next(c for c in calls if c[0] == "POST" and c[1].endswith("/api/v1/models/sync"))
    payload = sync_call[2]
    assert payload is not None
    assert payload["models"][0]["updated_at"] == 1767225600
    assert payload["models"][0]["created_at"] == 1767225600


def test_reconcile_200_empty_is_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_request(
        method: str,
        url: str,
        token: str | None = None,
        payload: dict[str, Any] | None = None,
        timeout: int = 30,
        retries: int = 3,
    ) -> tuple[int, object]:
        if url.endswith("/api/v1/models/export"):
            return 200, []
        if url.endswith("/api/v1/models/sync"):
            return 200, []
        raise AssertionError(f"unexpected url {url}")

    monkeypatch.setattr(mod, "request_json", fake_request)
    with pytest.raises(RuntimeError, match="empty list"):
        mod.reconcile("http://x", "token", "owner", [_chat_spec()], [])


def test_reconcile_import_fallback_only_on_404_405_501(monkeypatch: pytest.MonkeyPatch) -> None:
    for code in (404, 405, 501):
        calls: list[tuple[str, str, dict[str, Any] | None]] = []
        state: dict[str, Any] = {}

        def fake_request(
            method: str,
            url: str,
            token: str | None = None,
            payload: dict[str, Any] | None = None,
            timeout: int = 30,
            retries: int = 3,
            _code: int = code,
            _calls: list[tuple[str, str, dict[str, Any] | None]] = calls,
            _state: dict[str, Any] = state,
        ) -> tuple[int, object]:
            _calls.append((method, url, payload))
            if url.endswith("/api/v1/models/export"):
                return 200, _state.get("synced", [])
            if url.endswith("/api/v1/models/sync"):
                return _code, None
            if url.endswith("/api/v1/models/import"):
                synced = payload["models"] if payload else []
                _state["synced"] = synced
                return 200, synced
            raise AssertionError(f"unexpected url {url}")

        monkeypatch.setattr(mod, "request_json", fake_request)
        mod.reconcile("http://x", "token", "owner", [_chat_spec()], [])
        assert any(u.endswith("/api/v1/models/import") for _, u, _ in calls)


def test_reconcile_terminal_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    for code in (401, 403, 422):

        def fake_request(
            method: str,
            url: str,
            token: str | None = None,
            payload: dict[str, Any] | None = None,
            timeout: int = 30,
            retries: int = 3,
            _code: int = code,
        ) -> tuple[int, object]:
            if url.endswith("/api/v1/models/export"):
                return 200, []
            if url.endswith("/api/v1/models/sync"):
                return _code, None
            raise AssertionError(f"unexpected url {url}")

        monkeypatch.setattr(mod, "request_json", fake_request)
        with pytest.raises(RuntimeError, match="sync failed"):
            mod.reconcile("http://x", "token", "owner", [_chat_spec()], [])


def test_authenticate_admin_key_path(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_request(
        method: str,
        url: str,
        token: str | None = None,
        payload: dict[str, Any] | None = None,
        timeout: int = 30,
        retries: int = 3,
    ) -> tuple[int, object]:
        assert token == "sk-admin"
        return 200, {"id": "user-1"}

    monkeypatch.setattr(mod, "request_json", fake_request)
    token, owner = mod.authenticate("http://x", {"OPENWEBUI_ADMIN_API_KEY": "sk-admin"})
    assert token == "sk-admin"
    assert owner == "user-1"


def test_authenticate_empty_credential_signin(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_request(
        method: str,
        url: str,
        token: str | None = None,
        payload: dict[str, Any] | None = None,
        timeout: int = 30,
        retries: int = 3,
    ) -> tuple[int, object]:
        if url.endswith("/api/v1/users/user"):
            return 401, None
        if url.endswith("/api/v1/auths/signin"):
            assert payload == {"email": "", "password": ""}
            return 200, {"token": "jwt-token", "user": {"id": "user-2"}}
        raise AssertionError(f"unexpected url {url}")

    monkeypatch.setattr(mod, "request_json", fake_request)
    token, owner = mod.authenticate("http://x", {"OPENWEBUI_ADMIN_API_KEY": "sk-admin"})
    assert token == "jwt-token"
    assert owner == "user-2"


def test_request_json_retries_on_503(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"n": 0}

    def fake_urlopen(req: Request, timeout: int = 30) -> _FakeResponse:
        calls["n"] += 1
        if calls["n"] < 3:
            raise urllib.error.HTTPError(req.full_url, 503, "Service Unavailable", Message(), io.BytesIO(b"{}"))
        return _FakeResponse(200, b'{"ok": true}')

    monkeypatch.setattr(mod, "urlopen", fake_urlopen)
    status, body = mod.request_json("GET", "http://x/ready", retries=2)
    assert calls["n"] == 3
    assert status == 200
    assert body == {"ok": True}


def test_wait_ready_polls(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"n": 0}

    def fake_request(
        method: str,
        url: str,
        token: str | None = None,
        payload: dict[str, Any] | None = None,
        timeout: int = 30,
        retries: int = 3,
    ) -> tuple[int, object]:
        calls["n"] += 1
        if calls["n"] < 3:
            raise urllib.error.URLError("not ready")
        return 200, None

    monkeypatch.setattr(mod, "request_json", fake_request)
    mod.wait_ready("http://x", timeout=10)
    assert calls["n"] == 3


def test_load_group_data_requires_object(tmp_path: Path) -> None:
    p = tmp_path / "models.json"
    p.write_text("[1, 2]")
    with pytest.raises(ValueError, match="JSON object"):
        mod.load_group_data(str(p))


def test_load_group_data_roundtrip(tmp_path: Path) -> None:
    p = tmp_path / "models.json"
    p.write_text(json.dumps({"default_models": ["chat"], "model_map": {"chat": "router-chat"}}))
    data = mod.load_group_data(str(p))
    assert data["default_models"] == ["chat"]
