import importlib.util
import json
import os
from typing import Any
from unittest import mock
from urllib.error import HTTPError

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

CONFIG: dict[str, Any] = {
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
        "chat": "zen/deepseek-v4-flash",
        "chat_thinking": "zen/deepseek-v4-pro",
        "web_research": "zen/glm-5.3-flash",
        "translate_de": "zen/deepseek-v4-flash",
        "translate_en": "zen/deepseek-v4-flash",
        "fix_grammar_en": "zen/deepseek-v4-flash",
        "fix_grammar_de": "zen/deepseek-v4-flash",
        "linux_cli": "ollama/qwen2.5:3b",
    },
}

_PRESET_KEYS = {
    "id",
    "name",
    "base_model_id",
    "params",
    "tools",
    "meta",
    "access_grants",
    "is_active",
    "user_id",
    "updated_at",
    "created_at",
}


def _fake_response(status: int, body: Any) -> mock.MagicMock:
    resp = mock.MagicMock()
    resp.status = status
    resp.read.return_value = json.dumps(body).encode()
    resp.__enter__.return_value = resp
    return resp


def _yaml_model_names(path: str) -> set[str]:
    model_names: set[str] = set()
    with open(path) as f:
        for line in f:
            stripped = line.strip()
            if stripped.startswith("- "):
                stripped = stripped[2:]
            if stripped.startswith("model_name:"):
                model_names.add(stripped.split(":", 1)[1].strip())
    return model_names


def _yaml_litellm_models(path: str) -> list[str]:
    models: list[str] = []
    in_params = False
    with open(path) as f:
        for line in f:
            stripped = line.strip()
            if stripped == "litellm_params:":
                in_params = True
            elif in_params and stripped.startswith("model:"):
                models.append(stripped.split(":", 1)[1].strip())
            elif in_params and stripped and not stripped.startswith("api_"):
                in_params = False
    return models


def test_preset_payloads_normalized() -> None:
    payloads = mod.build_preset_payloads(CONFIG)
    assert [p["id"] for p in payloads] == CONFIG["default_models"]
    assert len(payloads) == 8
    for payload in payloads:
        assert payload["name"]
        assert payload["base_model_id"] == CONFIG["model_map"][payload["id"]]
        assert payload["params"]["system"]
        assert payload["access_grants"] == []
        assert payload["is_active"] is True
        assert payload["user_id"] == ""
        assert isinstance(payload["updated_at"], int)
        assert isinstance(payload["created_at"], int)
        assert set(payload.keys()) == _PRESET_KEYS
        if payload["id"] == "web_research":
            assert payload["tools"] == ["web_search"]
        else:
            assert payload["tools"] == []


def test_litellm_config_yaml() -> None:
    yaml_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "deploys",
        "openwebui",
        "files",
        "litellm-config.yaml",
    )
    assert _yaml_model_names(yaml_path) == set(CONFIG["model_map"].values())
    for model in _yaml_litellm_models(yaml_path):
        assert model.startswith("openai/") or model.startswith("ollama/")
    with open(yaml_path) as f:
        content = f.read()
    assert "master_key: os.environ/LITELLM_MASTER_KEY" in content
    assert "default_fallbacks:" in content
    assert "- zen/deepseek-v4-flash" in content


def test_sync_payload_shape() -> None:
    exported = [
        {
            "id": "custom-model",
            "name": "Custom",
            "base_model_id": "zen/other",
            "params": {"system": "x"},
            "tools": [],
            "meta": {},
            "access_grants": [],
            "is_active": True,
        },
        {
            "id": "another",
            "name": "Another",
            "base_model_id": "ollama/llama3",
            "params": {"system": "y"},
            "tools": [],
            "meta": {},
            "access_grants": [],
            "is_active": False,
        },
    ]
    payload = mod.build_sync_payload(exported, mod.build_preset_payloads(CONFIG))
    assert set(payload.keys()) == {"models"}
    models = payload["models"]
    assert [m["id"] for m in models[:8]] == CONFIG["default_models"]
    assert models[8:] == exported
    for preset in models[:8]:
        assert set(preset.keys()) == _PRESET_KEYS


def test_sync_200_empty_is_failure() -> None:
    def fake(request: Any, timeout: int = 30) -> mock.Mock:
        return _fake_response(200, [])

    with mock.patch.object(mod, "urlopen", side_effect=fake), mock.patch.object(mod.time, "sleep"):
        with pytest.raises(SystemExit):
            mod.reconcile("http://127.0.0.1:13307", CONFIG, {})


def test_auth_fallback_order() -> None:
    def fake_signin_ok(request: Any, timeout: int = 30) -> mock.Mock:
        url = request.full_url
        if url.endswith("/api/v1/models/export"):
            raise HTTPError(url, 401, "Unauthorized", mock.Mock(), None)
        if url.endswith("/api/v1/auths/signin"):
            return _fake_response(200, {"token": "jwt-token"})
        raise AssertionError(f"unexpected url: {url}")

    with mock.patch.object(mod, "urlopen", side_effect=fake_signin_ok):
        headers = mod.authenticate("http://127.0.0.1:13307", {})
    assert headers == {"Authorization": "Bearer jwt-token"}

    def fake_signin_fails(request: Any, timeout: int = 30) -> mock.Mock:
        url = request.full_url
        if url.endswith("/api/v1/models/export"):
            raise HTTPError(url, 401, "Unauthorized", mock.Mock(), None)
        if url.endswith("/api/v1/auths/signin"):
            raise HTTPError(url, 401, "Unauthorized", mock.Mock(), None)
        raise AssertionError(f"unexpected url: {url}")

    with mock.patch.object(mod, "urlopen", side_effect=fake_signin_fails):
        headers = mod.authenticate("http://127.0.0.1:13307", {"OPENWEBUI_ADMIN_API_KEY": "sk-test"})
    assert headers == {"Authorization": "Bearer sk-test"}


def test_connection_reset_is_retryable() -> None:
    calls = []

    def fake(request: Any, timeout: int = 30) -> mock.MagicMock:
        calls.append(request)
        if len(calls) == 1:
            raise ConnectionResetError("connection reset by peer")
        return _fake_response(200, [])

    with mock.patch.object(mod, "urlopen", side_effect=fake), mock.patch.object(mod.time, "sleep"):
        headers = mod.authenticate("http://127.0.0.1:13307", {})
    assert headers == {}


def test_request_json_sets_json_content_type() -> None:
    captured: dict[str, Any] = {}

    def fake(request: Any, timeout: int = 30) -> mock.MagicMock:
        captured["headers"] = dict(request.headers)
        return _fake_response(200, {"ok": True})

    with mock.patch.object(mod, "urlopen", side_effect=fake):
        status, body = mod.request_json(
            "http://127.0.0.1:13307/api/v1/auths/signin",
            method="POST",
            body={"email": "", "password": ""},
        )
    assert status == 200
    assert body == {"ok": True}
    assert captured["headers"]["Content-type"] == "application/json"


def test_collision_fails_before_mutation() -> None:
    exported = [
        {
            "id": "chat",
            "name": "Chat",
            "base_model_id": "zen/other",
            "params": {"system": "x"},
            "tools": [],
            "meta": {},
            "access_grants": [],
            "is_active": True,
        }
    ]
    with mock.patch.object(mod, "urlopen") as fake_urlopen:
        with pytest.raises(SystemExit):
            mod.build_sync_payload(exported, mod.build_preset_payloads(CONFIG))
    fake_urlopen.assert_not_called()
