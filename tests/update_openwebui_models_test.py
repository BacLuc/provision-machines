import argparse
import importlib.util
from email.message import Message
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPT = _REPO_ROOT / "scripts" / "update-openwebui-models.py"
_spec = importlib.util.spec_from_file_location("update_openwebui_models", _SCRIPT)
assert _spec is not None
assert _spec.loader is not None
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)

_HEADERS = Message()

_MODEL_MAP = {
    "chat": "router-chat",
    "chat_thinking": "router-chat-thinking",
    "web_research": "router-web-research",
    "translate_de": "router-translate-de",
    "translate_en": "router-translate-en",
    "fix_grammar_en": "router-fix-grammar-en",
    "fix_grammar_de": "router-fix-grammar-de",
    "linux_cli": "router-linux-cli",
}
_MODELS = [{"preset_id": preset, "router_model_id": router} for preset, router in _MODEL_MAP.items()]


class _FakeResponse:
    def __init__(self, body: bytes, status: int = 200) -> None:
        self._body = body
        self.status = status

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None


class _FakeTime:
    def __init__(self) -> None:
        self.now = 0.0

    def monotonic(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.now += seconds


def test_build_preset_specs() -> None:
    specs = mod.build_preset_specs(_MODELS)
    assert len(specs) == 8
    for spec in specs:
        assert spec["router_model_id"] == _MODEL_MAP[spec["preset_id"]]
        assert spec["name"]
        assert spec["prompt"]
    web_research = next(spec for spec in specs if spec["preset_id"] == "web_research")
    assert web_research["web_search"] is True
    assert all(spec["web_search"] is False for spec in specs if spec["preset_id"] != "web_research")


def test_build_preset_specs_rejects_id_collision() -> None:
    with pytest.raises(ValueError, match="must differ"):
        mod.build_preset_specs([{"preset_id": "chat", "router_model_id": "chat"}])


def test_build_preset_specs_rejects_unknown_preset() -> None:
    with pytest.raises(ValueError, match="unknown preset_id"):
        mod.build_preset_specs([{"preset_id": "nope", "router_model_id": "router-nope"}])


def test_to_sync_model_envelope() -> None:
    spec = mod.build_preset_specs([{"preset_id": "chat", "router_model_id": "router-chat"}])[0]
    rows = mod.to_sync_model(spec, "admin-1", {}, 1234)
    preset = rows["preset"]
    assert list(preset.keys()) == [
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
    assert preset["id"] == "chat"
    assert preset["user_id"] == "admin-1"
    assert preset["base_model_id"] == "router-chat"
    assert preset["params"]["system"] == spec["prompt"]
    assert "system" not in preset["meta"]
    assert preset["access_grants"] == []
    assert preset["is_active"] is True
    assert preset["updated_at"] == 1234
    assert preset["created_at"] == 1234
    base = rows["base"]
    assert base["id"] == "router-chat"
    assert base["base_model_id"] is None
    assert base["params"] == {}
    assert all(value is False for value in base["meta"]["capabilities"].values())


def test_to_sync_model_preserves_timestamps() -> None:
    spec = mod.build_preset_specs([{"preset_id": "chat", "router_model_id": "router-chat"}])[0]
    existing = {"chat": {"id": "chat", "updated_at": 111, "created_at": 222}}
    rows = mod.to_sync_model(spec, "admin-1", existing, 1234)
    assert rows["preset"]["updated_at"] == 111
    assert rows["preset"]["created_at"] == 222


def test_to_sync_model_web_research_flags() -> None:
    spec = mod.build_preset_specs([{"preset_id": "web_research", "router_model_id": "router-web-research"}])[0]
    preset = mod.to_sync_model(spec, "admin-1", {}, 1234)["preset"]
    capabilities = preset["meta"]["capabilities"]
    assert capabilities["web_search"] is True
    assert capabilities["supports_web_search"] is True
    assert preset["meta"]["defaultFeatureIds"] == ["web_search"]
    assert preset["meta"]["builtinTools"] == {"web_search": True}
    assert preset["params"]["function_calling"] == "native"
    for key, value in capabilities.items():
        if key not in ("web_search", "supports_web_search"):
            assert value is False


def test_to_sync_model_non_web_research_flags() -> None:
    spec = mod.build_preset_specs([{"preset_id": "chat", "router_model_id": "router-chat"}])[0]
    preset = mod.to_sync_model(spec, "admin-1", {}, 1234)["preset"]
    assert all(value is False for value in preset["meta"]["capabilities"].values())
    assert preset["meta"]["defaultFeatureIds"] == []
    assert preset["meta"]["builtinTools"] == {}
    assert "function_calling" not in preset["params"]


def test_parse_litellm_model_names_from_config() -> None:
    text = (_REPO_ROOT / "deploys" / "openwebui" / "files" / "litellm-config.yaml").read_text()
    names = mod.parse_litellm_model_names(text)
    assert len(names) == 16
    assert set(names) == set(_MODEL_MAP.values())


def test_parse_litellm_model_names_rejects_tabs() -> None:
    with pytest.raises(mod.YamlParseError):
        mod.parse_litellm_model_names("model_list:\n\t- model_name: x\n")


def test_parse_litellm_model_names_rejects_anchors() -> None:
    with pytest.raises(mod.YamlParseError):
        mod.parse_litellm_model_names("model_list:\n  - model_name: &anchor x\n")


def test_parse_litellm_model_names_rejects_flow_style() -> None:
    with pytest.raises(mod.YamlParseError):
        mod.parse_litellm_model_names("model_list:\n  - model_name: [x]\n")


def test_parse_litellm_model_names_rejects_duplicate_keys() -> None:
    with pytest.raises(mod.YamlParseError):
        mod.parse_litellm_model_names("model_list:\n  - model_name: a\n    model_name: b\n")


def test_parse_litellm_model_names_rejects_malformed_indentation() -> None:
    with pytest.raises(mod.YamlParseError):
        mod.parse_litellm_model_names(
            "model_list:\n  - model_name: a\n    litellm_params:\n      model: os.environ/X\n     api_base: os.environ/Y\n"
        )


def test_read_env_file(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("BRAVE_API_KEY=secret-brave\nLITELLM_MASTER_KEY=secret-master\n# comment\nEMPTY=\n")
    assert mod.read_env_file(str(env_file)) == {
        "BRAVE_API_KEY": "secret-brave",
        "LITELLM_MASTER_KEY": "secret-master",
        "EMPTY": "",
    }


def test_read_env_file_never_prints_secrets(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("LITELLM_MASTER_KEY=super-secret-value\n")
    mod.read_env_file(str(env_file))
    captured = capsys.readouterr()
    assert "super-secret-value" not in captured.out
    assert "super-secret-value" not in captured.err


def test_reconcile_sync_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    unrelated = {
        "id": "unrelated",
        "user_id": "u1",
        "name": "Unrelated",
        "params": {},
        "meta": {},
        "is_active": True,
        "updated_at": 1,
        "created_at": 1,
    }
    exported: list[dict[str, Any]] = [unrelated]
    calls: list[tuple[str, str, dict[str, Any] | None]] = []

    def fake_request_json(method: str, url: str, token: str, payload: dict[str, Any] | None = None) -> Any:
        nonlocal exported
        calls.append((method, url, payload))
        if url.endswith("/api/v1/models/export"):
            return exported
        if url.endswith("/api/v1/users/"):
            return {"users": [{"id": "admin-1", "role": "admin"}]}
        if url.endswith("/api/v1/models/sync"):
            assert payload is not None
            exported = payload["models"]
            return payload["models"]
        return None

    monkeypatch.setattr(mod, "request_json", fake_request_json)
    args = argparse.Namespace(base_url="http://x", admin_api_key="", models=_MODELS, dry_run=False)
    mod.reconcile(args, "token")
    sync_call = next(call for call in calls if call[0] == "POST" and call[1].endswith("/api/v1/models/sync"))
    body = sync_call[2]
    assert body is not None
    ids = [row["id"] for row in body["models"]]
    expected = []
    for preset, router in _MODEL_MAP.items():
        expected.append(preset)
        expected.append(router)
    expected.append("unrelated")
    assert ids == expected
    preserved = body["models"][-1]
    assert preserved["id"] == "unrelated"
    assert preserved["user_id"] == "u1"
    assert preserved["base_model_id"] is None
    assert preserved["name"] == "Unrelated"
    assert preserved["params"] == {}
    assert preserved["meta"] == {}
    assert preserved["access_grants"] == []
    assert preserved["is_active"] is True
    assert preserved["updated_at"] == 1
    assert preserved["created_at"] == 1


def test_normalize_preserved_info_envelope() -> None:
    row = {
        "id": "other",
        "info": {
            "base_model_id": "openai/gpt-4o",
            "params": {"system": "s"},
            "meta": {"capabilities": {"web_search": False}},
            "updated_at": 1767225600,
            "created_at": 1767225600,
        },
    }
    normalized = mod.normalize_preserved(row, "admin-1")
    assert normalized["id"] == "other"
    assert normalized["user_id"] == "admin-1"
    assert normalized["base_model_id"] == "openai/gpt-4o"
    assert normalized["name"] == ""
    assert normalized["params"] == {"system": "s"}
    assert normalized["meta"] == {"capabilities": {"web_search": False}}
    assert normalized["access_grants"] == []
    assert normalized["is_active"] is True
    assert normalized["updated_at"] == 1767225600
    assert normalized["created_at"] == 1767225600


def test_normalize_preserved_missing_fields_defaults() -> None:
    normalized = mod.normalize_preserved({"id": "other"}, "admin-1")
    assert normalized["user_id"] == "admin-1"
    assert normalized["base_model_id"] is None
    assert normalized["name"] == ""
    assert normalized["params"] == {}
    assert normalized["meta"] == {}
    assert normalized["access_grants"] == []
    assert normalized["is_active"] is True
    assert isinstance(normalized["updated_at"], int)
    assert isinstance(normalized["created_at"], int)


def test_reconcile_empty_sync_response_is_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_request_json(method: str, url: str, token: str, payload: dict[str, Any] | None = None) -> Any:
        if url.endswith("/api/v1/models/export"):
            return []
        if url.endswith("/api/v1/users/"):
            return {"users": [{"id": "admin-1", "role": "admin"}]}
        if url.endswith("/api/v1/models/sync"):
            return []
        return None

    monkeypatch.setattr(mod, "request_json", fake_request_json)
    args = argparse.Namespace(base_url="http://x", admin_api_key="", models=_MODELS, dry_run=False)
    with pytest.raises(RuntimeError, match="empty result"):
        mod.reconcile(args, "token")


def test_reconcile_import_fallback_on_404(monkeypatch: pytest.MonkeyPatch) -> None:
    import_calls: list[dict[str, Any]] = []
    exported: list[dict[str, Any]] = []

    def fake_request_json(method: str, url: str, token: str, payload: dict[str, Any] | None = None) -> Any:
        nonlocal exported
        if url.endswith("/api/v1/models/export"):
            return exported
        if url.endswith("/api/v1/users/"):
            return {"users": [{"id": "admin-1", "role": "admin"}]}
        if url.endswith("/api/v1/models/sync"):
            raise HTTPError(url, 404, "Not Found", _HEADERS, None)
        if url.endswith("/api/v1/models/import"):
            assert payload is not None
            import_calls.append(payload)
            exported.extend(payload["models"])
            return True
        return None

    monkeypatch.setattr(mod, "request_json", fake_request_json)
    args = argparse.Namespace(base_url="http://x", admin_api_key="", models=_MODELS, dry_run=False)
    mod.reconcile(args, "token")
    assert len(import_calls) == 16


def test_reconcile_import_fallback_only_on_404_405_501(monkeypatch: pytest.MonkeyPatch) -> None:
    for code in (401, 403, 422):
        import_calls: list[dict[str, Any]] = []

        def fake_request_json(
            method: str,
            url: str,
            token: str,
            payload: dict[str, Any] | None = None,
            code: int = code,
            import_calls: list[dict[str, Any]] = import_calls,
        ) -> Any:
            if url.endswith("/api/v1/models/export"):
                return []
            if url.endswith("/api/v1/users/"):
                return {"users": [{"id": "admin-1", "role": "admin"}]}
            if url.endswith("/api/v1/models/sync"):
                raise HTTPError(url, code, "Error", _HEADERS, None)
            if url.endswith("/api/v1/models/import"):
                assert payload is not None
                import_calls.append(payload)
                return True
            return None

        monkeypatch.setattr(mod, "request_json", fake_request_json)
        args = argparse.Namespace(base_url="http://x", admin_api_key="", models=_MODELS, dry_run=False)
        with pytest.raises(HTTPError):
            mod.reconcile(args, "token")
        assert import_calls == []


def test_reconcile_idempotent(monkeypatch: pytest.MonkeyPatch) -> None:
    exported: list[dict[str, Any]] = [
        {
            "id": "unrelated",
            "user_id": "u1",
            "name": "Unrelated",
            "params": {},
            "meta": {},
            "is_active": True,
            "updated_at": 1,
            "created_at": 1,
        }
    ]
    synced: dict[str, Any] | None = None

    def fake_request_json(method: str, url: str, token: str, payload: dict[str, Any] | None = None) -> Any:
        nonlocal exported, synced
        if url.endswith("/api/v1/models/export"):
            return exported
        if url.endswith("/api/v1/users/"):
            return {"users": [{"id": "admin-1", "role": "admin"}]}
        if url.endswith("/api/v1/models/sync"):
            assert payload is not None
            synced = payload
            exported = payload["models"]
            return payload["models"]
        return None

    monkeypatch.setattr(mod, "request_json", fake_request_json)
    args = argparse.Namespace(base_url="http://x", admin_api_key="", models=_MODELS, dry_run=False)
    mod.reconcile(args, "token")
    first = synced
    mod.reconcile(args, "token")
    assert synced == first


def test_authenticate_admin_key(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, str, str]] = []

    def fake_request_json(method: str, url: str, token: str, payload: dict[str, Any] | None = None) -> Any:
        calls.append((method, url, token))
        if url.endswith("/api/v1/users/"):
            return {"users": [{"id": "admin-1", "role": "admin"}]}
        return None

    monkeypatch.setattr(mod, "request_json", fake_request_json)
    args = argparse.Namespace(base_url="http://x", admin_api_key="admin-key", models=[], dry_run=False)
    assert mod.authenticate(args, {}) == "admin-key"
    assert calls == [("GET", "http://x/api/v1/users/", "admin-key")]


def test_authenticate_env_key(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_request_json(method: str, url: str, token: str, payload: dict[str, Any] | None = None) -> Any:
        if url.endswith("/api/v1/users/"):
            return {"users": [{"id": "admin-1", "role": "admin"}]}
        return None

    monkeypatch.setattr(mod, "request_json", fake_request_json)
    args = argparse.Namespace(base_url="http://x", admin_api_key="", models=[], dry_run=False)
    assert mod.authenticate(args, {"OPENWEBUI_ADMIN_API_KEY": "env-key"}) == "env-key"


def test_authenticate_signin_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, str, str, dict[str, Any] | None]] = []

    def fake_request_json(method: str, url: str, token: str, payload: dict[str, Any] | None = None) -> Any:
        calls.append((method, url, token, payload))
        if url.endswith("/api/v1/auths/signin"):
            return {"token": "jwt-token"}
        return None

    monkeypatch.setattr(mod, "request_json", fake_request_json)
    args = argparse.Namespace(base_url="http://x", admin_api_key="", models=[], dry_run=False)
    assert mod.authenticate(args, {}) == "jwt-token"
    assert calls[0] == ("POST", "http://x/api/v1/auths/signin", "", {"email": "", "password": ""})


def test_authenticate_falls_back_to_signin_on_bearer_401(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, str, str, dict[str, Any] | None]] = []

    def fake_request_json(method: str, url: str, token: str, payload: dict[str, Any] | None = None) -> Any:
        calls.append((method, url, token, payload))
        if url.endswith("/api/v1/users/"):
            raise HTTPError(url, 401, "Unauthorized", _HEADERS, None)
        return {"token": "jwt-token"}

    monkeypatch.setattr(mod, "request_json", fake_request_json)
    args = argparse.Namespace(base_url="http://x", admin_api_key="admin-key", models=[], dry_run=False)
    assert mod.authenticate(args, {}) == "jwt-token"
    assert calls == [
        ("GET", "http://x/api/v1/users/", "admin-key", None),
        ("POST", "http://x/api/v1/auths/signin", "", {"email": "", "password": ""}),
    ]


def test_authenticate_both_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_request_json(method: str, url: str, token: str, payload: dict[str, Any] | None = None) -> Any:
        raise HTTPError(url, 401, "Unauthorized", _HEADERS, None)

    monkeypatch.setattr(mod, "request_json", fake_request_json)
    args = argparse.Namespace(base_url="http://x", admin_api_key="", models=[], dry_run=False)
    with pytest.raises(RuntimeError, match="set OPENWEBUI_ADMIN_API_KEY in local.py"):
        mod.authenticate(args, {})


def test_request_json_retries_on_urlerror(monkeypatch: pytest.MonkeyPatch) -> None:
    attempts = {"n": 0}

    def fake_urlopen(req: Any, timeout: int = 30) -> _FakeResponse:
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise URLError("connection refused")
        return _FakeResponse(b'{"ok": true}')

    monkeypatch.setattr(mod, "urlopen", fake_urlopen)
    monkeypatch.setattr(mod, "_MAX_ATTEMPTS", 5)
    monkeypatch.setattr(mod, "_BACKOFF_SECONDS", 0)
    assert mod.request_json("GET", "http://x", "") == {"ok": True}
    assert attempts["n"] == 3


def test_request_json_retries_on_503(monkeypatch: pytest.MonkeyPatch) -> None:
    attempts = {"n": 0}

    def fake_urlopen(req: Any, timeout: int = 30) -> _FakeResponse:
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise HTTPError("http://x", 503, "Service Unavailable", _HEADERS, None)
        return _FakeResponse(b'{"ok": true}')

    monkeypatch.setattr(mod, "urlopen", fake_urlopen)
    monkeypatch.setattr(mod, "_MAX_ATTEMPTS", 5)
    monkeypatch.setattr(mod, "_BACKOFF_SECONDS", 0)
    assert mod.request_json("GET", "http://x", "") == {"ok": True}
    assert attempts["n"] == 3


def test_request_json_retries_on_429(monkeypatch: pytest.MonkeyPatch) -> None:
    attempts = {"n": 0}

    def fake_urlopen(req: Any, timeout: int = 30) -> _FakeResponse:
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise HTTPError("http://x", 429, "Too Many Requests", _HEADERS, None)
        return _FakeResponse(b'{"ok": true}')

    monkeypatch.setattr(mod, "urlopen", fake_urlopen)
    monkeypatch.setattr(mod, "_MAX_ATTEMPTS", 5)
    monkeypatch.setattr(mod, "_BACKOFF_SECONDS", 0)
    assert mod.request_json("GET", "http://x", "") == {"ok": True}
    assert attempts["n"] == 3


def test_request_json_raises_after_retry_window(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(req: Any, timeout: int = 30) -> _FakeResponse:
        raise URLError("connection refused")

    monkeypatch.setattr(mod, "urlopen", fake_urlopen)
    monkeypatch.setattr(mod, "_MAX_ATTEMPTS", 3)
    monkeypatch.setattr(mod, "_BACKOFF_SECONDS", 0)
    with pytest.raises(URLError):
        mod.request_json("GET", "http://x", "")


def test_wait_ready_polls_until_200(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_time = _FakeTime()
    monkeypatch.setattr(mod, "time", fake_time)
    attempts = {"n": 0}

    def fake_urlopen(url: str, timeout: int = 30) -> _FakeResponse:
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise URLError("not ready")
        return _FakeResponse(b"ok", status=200)

    monkeypatch.setattr(mod, "urlopen", fake_urlopen)
    mod.wait_ready("http://x", timeout=300)
    assert attempts["n"] == 3


def test_wait_ready_retries_on_connection_reset(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_time = _FakeTime()
    monkeypatch.setattr(mod, "time", fake_time)
    attempts = {"n": 0}

    def fake_urlopen(url: str, timeout: int = 30) -> _FakeResponse:
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise ConnectionResetError("Connection reset by peer")
        return _FakeResponse(b"ok", status=200)

    monkeypatch.setattr(mod, "urlopen", fake_urlopen)
    mod.wait_ready("http://x", timeout=300)
    assert attempts["n"] == 3


def test_wait_ready_times_out(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_time = _FakeTime()
    monkeypatch.setattr(mod, "time", fake_time)

    def fake_urlopen(url: str, timeout: int = 30) -> _FakeResponse:
        raise URLError("not ready")

    monkeypatch.setattr(mod, "urlopen", fake_urlopen)
    with pytest.raises(RuntimeError, match="not ready"):
        mod.wait_ready("http://x", timeout=10)
