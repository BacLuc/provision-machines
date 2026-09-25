#!/usr/bin/env python3
"""Reconcile the declarative OpenWebUI model presets against a running OpenWebUI.

Reads the manifest, the AISIX resources file and the mode-600 .env, then rewrites the
OpenWebUI model table so it matches the eight presets. /models/sync prunes everything it
is not given, so every unrelated row is re-sent; when sync is unavailable (404/405/501)
the script falls back to the additive /models/import endpoint and deletes stale rows one
by one, which cannot prune, so the final export is the only exact verification.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

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
DEFAULT_URL = "http://127.0.0.1:13307"
ENV_FILE_MODE = 0o600


def _as_dict(value: object, name: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object")
    return cast(dict[str, object], value)


def _as_list(value: object, name: str) -> list[object]:
    if not isinstance(value, list):
        raise ValueError(f"{name} must be a list")
    return cast(list[object], value)


def _as_str(value: object, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _as_bool(value: object, name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be a boolean")
    return value


def _as_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer")
    return value


def _yaml_scalar(value: str, name: str) -> str:
    value = value.strip()
    if not value or value.startswith(("[", "{", "&", "*", "!", "|", ">")):
        raise ValueError(f"unsupported YAML value for {name}")
    if value.startswith(('"', "'")):
        if len(value) < 2 or value[-1] != value[0]:
            raise ValueError(f"unterminated YAML value for {name}")
        if value[0] == '"':
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError as error:
                raise ValueError(f"invalid YAML value for {name}") from error
            if not isinstance(parsed, str):
                raise ValueError(f"invalid YAML value for {name}")
            return parsed
        return value[1:-1].replace("''", "'")
    return value


def _manifest_parts(manifest: dict[str, object]) -> tuple[list[str], dict[str, str], list[dict[str, object]]]:
    default_models = [
        _as_str(value, "default_models") for value in _as_list(manifest.get("default_models"), "default_models")
    ]
    model_map_value = _as_dict(manifest.get("model_map"), "model_map")
    model_map = {key: _as_str(value, f"model_map.{key}") for key, value in model_map_value.items()}
    presets = [_as_dict(value, "presets") for value in _as_list(manifest.get("presets"), "presets")]
    if default_models != MODEL_IDS:
        raise ValueError("default_models must contain the eight fixed IDs in order")
    if list(model_map) != MODEL_IDS:
        raise ValueError("model_map must contain the eight fixed IDs in order")
    if [preset.get("id") for preset in presets] != MODEL_IDS:
        raise ValueError("presets must contain the eight fixed IDs in order")
    return default_models, model_map, presets


def _reject_secret_fields(value: object) -> None:
    if isinstance(value, dict):
        for key, child in cast(dict[str, object], value).items():
            if any(word in key.lower() for word in ("key", "token", "secret", "password")):
                raise ValueError("manifest must not contain secret fields")
            _reject_secret_fields(child)
    elif isinstance(value, list):
        for child in cast(list[object], value):
            _reject_secret_fields(child)


def load_manifest(path: str | os.PathLike[str]) -> dict[str, object]:
    value: object = json.loads(Path(path).read_text(encoding="utf-8"))
    manifest = _as_dict(value, "manifest")
    _reject_secret_fields(manifest)
    _manifest_parts(manifest)
    return manifest


def _parse_resource_models(lines: list[str]) -> dict[str, list[str]]:
    routes: dict[str, list[str]] = {}
    names: set[str] = set()
    current: str | None = None
    in_models = False
    in_routing = False
    in_targets = False
    route_settings: dict[str, dict[str, object]] = {}
    routing_names: set[str] = set()

    for raw_line in lines:
        if "\t" in raw_line or "\r" in raw_line:
            raise ValueError("AISIX resources must use space indentation")
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        if indent == 0:
            if stripped == "models:":
                in_models = True
                continue
            if in_models:
                break
            continue
        if not in_models:
            continue
        if indent == 2 and stripped.startswith("- display_name:"):
            if current is not None and current in routing_names:
                settings = route_settings[current]
                if settings != {
                    "strategy": "failover",
                    "retries": 0,
                    "max_fallbacks": 1,
                    "retry_on_429": True,
                }:
                    raise ValueError(f"invalid routing settings for {current}")
            current = _yaml_scalar(stripped.split(":", 1)[1], "display_name")
            if "${" in current or current in names:
                raise ValueError("model display names must be unique literals")
            names.add(current)
            routes[current] = []
            in_routing = False
            in_targets = False
            if current not in routing_names:
                route_settings.pop(current, None)
            continue
        if current is None:
            raise ValueError("model fields must follow a display_name")
        if indent == 4 and stripped.startswith("routing:"):
            if stripped != "routing:" or current in routes and routes[current]:
                raise ValueError("invalid routing block")
            in_routing = True
            routing_names.add(current)
            route_settings[current] = {}
            continue
        if indent == 4 and stripped.split(":", 1)[0] in {"provider", "adapter", "model_name", "provider_key"}:
            _yaml_scalar(stripped.split(":", 1)[1], "model field")
            continue
        if not in_routing:
            raise ValueError("unsupported model field")
        if indent == 6 and stripped.startswith("strategy:"):
            if route_settings[current].get("strategy") is not None:
                raise ValueError("duplicate routing strategy")
            route_settings[current]["strategy"] = _yaml_scalar(stripped.split(":", 1)[1], "strategy")
            continue
        if indent == 6 and stripped == "targets:":
            in_targets = True
            continue
        if indent == 8 and stripped.startswith("- model:"):
            if not in_targets:
                raise ValueError("routing target is outside targets")
            target = _yaml_scalar(stripped.split(":", 1)[1], "routing target")
            if "${" in target or target in routes[current]:
                raise ValueError("routing targets must be unique literals")
            routes[current].append(target)
            continue
        if indent == 6 and stripped.startswith(("retries:", "max_fallbacks:", "retry_on_429:")):
            key, value = stripped.split(":", 1)
            parsed: object
            if key == "retry_on_429":
                parsed = _yaml_scalar(value, key) == "true"
            else:
                try:
                    parsed = int(_yaml_scalar(value, key))
                except ValueError as error:
                    raise ValueError(f"invalid {key}") from error
            route_settings[current][key] = parsed
            continue
        if indent == 10 and stripped.startswith("priority:"):
            try:
                int(_yaml_scalar(stripped.split(":", 1)[1], "priority"))
            except ValueError as error:
                raise ValueError("routing priority must be an integer") from error
            continue
        raise ValueError("unsupported AISIX model structure")

    if current is not None and current in routing_names:
        settings = route_settings[current]
        if settings != {
            "strategy": "failover",
            "retries": 0,
            "max_fallbacks": 1,
            "retry_on_429": True,
        }:
            raise ValueError(f"invalid routing settings for {current}")
    for targets in routes.values():
        for target in targets:
            if target not in names:
                raise ValueError(f"routing target is not declared: {target}")
    return {name: targets for name, targets in routes.items() if targets}


def parse_aisix_model_names(path: str | os.PathLike[str]) -> dict[str, list[str]]:
    text = Path(path).read_text(encoding="utf-8")
    lines = text.splitlines()
    if not any(line.strip() in {'_format_version: "1"', "_format_version: 1"} for line in lines):
        raise ValueError("AISIX resources must declare format version 1")
    if any(line.lstrip().startswith(("[", "{", "&", "*")) for line in lines):
        raise ValueError("unsupported YAML syntax")
    return _parse_resource_models(lines)


def validate_router_models(manifest: dict[str, object], routes: dict[str, list[str]]) -> None:
    default_models, model_map, _ = _manifest_parts(manifest)
    aliases = [model_map[model_id] for model_id in default_models]
    if len(set(aliases)) != len(aliases):
        raise ValueError("router aliases must be distinct")
    for model_id, alias in zip(default_models, aliases, strict=True):
        if alias == model_id:
            raise ValueError(f"router alias collides with preset ID {model_id}")
        if alias not in routes or not routes[alias]:
            raise ValueError(f"router alias is missing from AISIX resources: {alias}")


def _existing_models(existing: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    result: dict[str, dict[str, object]] = {}
    for model in existing:
        model_id = model.get("id")
        if isinstance(model_id, str):
            if model_id in result:
                raise ValueError(f"duplicate exported model ID: {model_id}")
            result[model_id] = model
    return result


def _model_meta(web_search: bool) -> dict[str, object]:
    return {
        "capabilities": {
            "vision": False,
            "citations": web_search,
            "web_search": web_search,
            "image_generation": False,
            "code_interpreter": False,
        },
        "defaultFeatureIds": ["web_search"] if web_search else [],
        "builtinTools": {"web_search": web_search},
    }


def build_models(
    manifest: dict[str, object],
    existing: list[dict[str, object]],
    *,
    user_id: str,
    now: int,
) -> list[dict[str, object]]:
    default_models, model_map, presets = _manifest_parts(manifest)
    existing_by_id = _existing_models(existing)
    result: list[dict[str, object]] = []
    for model_id, preset in zip(default_models, presets, strict=True):
        previous = existing_by_id.get(model_id)
        if previous is not None and (
            previous.get("base_model_id") is None or previous.get("base_model_id") not in model_map.values()
        ):
            raise ValueError(f"desired model ID collides with a non-managed model: {model_id}")
        web_search = _as_bool(preset.get("web_search"), f"presets.{model_id}.web_search")
        params: dict[str, object] = {"system": _as_str(preset.get("system"), f"presets.{model_id}.system")}
        if web_search:
            params["function_calling"] = "native"
        model: dict[str, object] = {
            "id": model_id,
            "user_id": previous.get("user_id", user_id) if previous is not None else user_id,
            "base_model_id": model_map[model_id],
            "name": _as_str(preset.get("name"), f"presets.{model_id}.name"),
            "params": params,
            "meta": _model_meta(web_search),
            "access_grants": previous.get("access_grants", []) if previous is not None else [],
            "is_active": True,
            "updated_at": previous.get("updated_at", now) if previous is not None else now,
            "created_at": previous.get("created_at", now) if previous is not None else now,
        }
        result.append(model)
    return result


def build_sync_payload(
    manifest: dict[str, object],
    existing: list[dict[str, object]],
    *,
    user_id: str,
    now: int,
) -> list[dict[str, object]]:
    _, model_map, _ = _manifest_parts(manifest)
    aliases = set(model_map.values())
    managed = build_models(manifest, existing, user_id=user_id, now=now)
    managed_ids = {model["id"] for model in managed}
    preserved = [
        dict(model)
        for model in existing
        if model.get("id") not in managed_ids
        and (model.get("base_model_id") is None or model.get("base_model_id") not in aliases)
    ]
    return managed + preserved


def read_env_file(path: str | os.PathLike[str]) -> dict[str, str]:
    env_path = Path(path)
    mode = stat.S_IMODE(env_path.stat().st_mode)
    if mode != ENV_FILE_MODE:
        raise PermissionError("environment file must not be accessible by group or others")
    result: dict[str, str] = {}
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError("invalid environment file line")
        key, value = line.split("=", 1)
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
            raise ValueError("invalid environment variable name")
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        result[key] = value
    return result


class ReconciliationError(RuntimeError):
    pass


class HttpStatusError(ReconciliationError):
    def __init__(self, status: int) -> None:
        super().__init__(f"HTTP request failed with status {status}")
        self.status = status


def request_json(
    method: str,
    url: str,
    *,
    token: str | None = None,
    api_key: str | None = None,
    payload: object | None = None,
    headers: dict[str, str] | None = None,
    attempts: int = 3,
    backoff: float = 1.0,
    opener: Callable[..., Any] = urlopen,
    sleep: Callable[[float], None] = time.sleep,
) -> object:
    if attempts < 1:
        raise ValueError("attempts must be positive")
    request_headers = {"Accept": "application/json"}
    if headers:
        request_headers.update(headers)
    if token:
        request_headers["Authorization"] = f"Bearer {token}"
    if api_key:
        request_headers["x-api-key"] = api_key
    body = None
    if payload is not None:
        body = json.dumps(payload, separators=(",", ":")).encode()
        request_headers["Content-Type"] = "application/json"
    request = Request(url, data=body, headers=request_headers, method=method)
    for attempt in range(attempts):
        try:
            with opener(request, timeout=30) as response:
                raw = response.read()
            if not raw:
                return None
            value: object = json.loads(raw)
            return value
        except HTTPError as error:
            status = error.code
            if status in {429, 503} and attempt + 1 < attempts:
                sleep(backoff * (2**attempt))
                continue
            raise HttpStatusError(status) from None
        except URLError:
            if attempt + 1 < attempts:
                sleep(backoff * (2**attempt))
                continue
            raise ReconciliationError("network request failed") from None
    raise ReconciliationError("network request failed")


def _response_user_id(value: object) -> str:
    response = _as_dict(value, "authentication response")
    user_id = response.get("id")
    if isinstance(user_id, str) and user_id:
        return user_id
    user = response.get("user")
    if isinstance(user, dict):
        nested_id = user.get("id")
        if isinstance(nested_id, str) and nested_id:
            return nested_id
    raise ReconciliationError("authentication response did not identify an admin user")


def authenticate(
    base_url: str,
    env: dict[str, str],
    *,
    opener: Callable[..., Any] = urlopen,
    sleep: Callable[[float], None] = time.sleep,
) -> tuple[dict[str, str], str]:
    base = base_url.rstrip("/")
    api_key = env.get("OPENWEBUI_ADMIN_API_KEY", "")
    if api_key:
        user = request_json(
            "GET",
            f"{base}/api/v1/auths/user",
            api_key=api_key,
            opener=opener,
            sleep=sleep,
        )
        return {"x-api-key": api_key}, _response_user_id(user)
    signin = request_json(
        "POST",
        f"{base}/api/v1/auths/signin",
        payload={"email": "", "password": ""},
        opener=opener,
        sleep=sleep,
    )
    response = _as_dict(signin, "authentication response")
    token = response.get("token")
    if not isinstance(token, str) or not token:
        raise ReconciliationError("authentication response did not include a token")
    verified = request_json(
        "GET",
        f"{base}/api/v1/auths/user",
        token=token,
        opener=opener,
        sleep=sleep,
    )
    return {"Authorization": f"Bearer {token}"}, _response_user_id(verified)


def wait_ready(
    base_url: str,
    headers: dict[str, str],
    *,
    attempts: int = 12,
    backoff: float = 5.0,
    opener: Callable[..., Any] = urlopen,
    sleep: Callable[[float], None] = time.sleep,
) -> None:
    if attempts < 1:
        raise ValueError("attempts must be positive")
    url = f"{base_url.rstrip('/')}/ready"
    for attempt in range(attempts):
        try:
            request_json("GET", url, headers=headers, attempts=1, opener=opener, sleep=sleep)
            return
        except ReconciliationError:
            if attempt + 1 == attempts:
                raise ReconciliationError("OpenWebUI did not become ready") from None
            sleep(min(backoff * (2**attempt), 30))


def _model_list(value: object, name: str) -> list[dict[str, object]]:
    return [_as_dict(item, name) for item in _as_list(value, name)]


def _matches_expected(actual: object, expected: object) -> bool:
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return False
        actual_dict = cast(dict[str, object], actual)
        expected_dict = cast(dict[str, object], expected)
        return all(
            key in actual_dict and _matches_expected(actual_dict[key], value) for key, value in expected_dict.items()
        )
    if isinstance(expected, list):
        return actual == expected
    return actual == expected


def verify_models(expected: list[dict[str, object]], actual: list[dict[str, object]]) -> None:
    expected_by_id = {str(model["id"]): model for model in expected}
    actual_by_id: dict[str, dict[str, object]] = {}
    for model in actual:
        model_id = model.get("id")
        if not isinstance(model_id, str) or model_id in actual_by_id:
            raise ReconciliationError("model export contained duplicate or invalid IDs")
        actual_by_id[model_id] = model
    if not set(expected_by_id).issubset(actual_by_id):
        missing = sorted(set(expected_by_id) - set(actual_by_id))
        raise ReconciliationError(f"model export is missing managed IDs: {', '.join(missing)}")
    managed_order = [model_id for model_id in actual_by_id if model_id in expected_by_id]
    if managed_order != list(expected_by_id):
        raise ReconciliationError("model export changed the managed preset order")
    required = (
        "id",
        "user_id",
        "base_model_id",
        "name",
        "params",
        "meta",
        "access_grants",
        "is_active",
        "created_at",
    )
    for model_id, expected_model in expected_by_id.items():
        actual_model = actual_by_id[model_id]
        for key in required:
            if not _matches_expected(actual_model.get(key), expected_model.get(key)):
                raise ReconciliationError(f"model export did not match managed field: {model_id}.{key}")


def reconcile(
    base_url: str,
    manifest: dict[str, object],
    resources_path: str | os.PathLike[str],
    env_path: str | os.PathLike[str],
    *,
    opener: Callable[..., Any] = urlopen,
    sleep: Callable[[float], None] = time.sleep,
    now: int | None = None,
) -> list[dict[str, object]]:
    base = base_url.rstrip("/")
    routes = parse_aisix_model_names(resources_path)
    validate_router_models(manifest, routes)
    env = read_env_file(env_path)
    wait_ready(base, {}, opener=opener, sleep=sleep)
    auth_headers, user_id = authenticate(base, env, opener=opener, sleep=sleep)
    pre_export = _model_list(
        request_json("GET", f"{base}/api/v1/models/export", headers=auth_headers, opener=opener, sleep=sleep),
        "model export",
    )
    all_rows = _model_list(
        request_json("GET", f"{base}/api/v1/models/all", headers=auth_headers, opener=opener, sleep=sleep),
        "model list",
    )
    timestamp = int(time.time()) if now is None else now
    desired = build_models(manifest, all_rows, user_id=user_id, now=timestamp)
    synced_models = build_sync_payload(manifest, all_rows, user_id=user_id, now=timestamp)
    payload_ids = {str(model["id"]) for model in synced_models}
    _, model_map, _ = _manifest_parts(manifest)
    aliases = set(model_map.values())
    managed_ids = {model["id"] for model in desired}
    preserved_before = {
        str(model.get("id"))
        for model in pre_export
        if model.get("id") not in managed_ids and model.get("base_model_id") not in aliases
    }
    try:
        sync_result = request_json(
            "POST",
            f"{base}/api/v1/models/sync",
            headers=auth_headers,
            payload={"models": synced_models},
            opener=opener,
            sleep=sleep,
        )
        if not isinstance(sync_result, list) or not sync_result:
            raise ReconciliationError("OpenWebUI returned an empty or invalid model sync response")
        synced_ids = {str(model.get("id")) for model in _model_list(sync_result, "model sync response")}
        if synced_ids != payload_ids:
            raise ReconciliationError("OpenWebUI model sync response did not match the submitted models")
    except HttpStatusError as error:
        if error.status not in {404, 405, 501}:
            raise
        imported = request_json(
            "POST",
            f"{base}/api/v1/models/import",
            headers=auth_headers,
            payload={"models": desired},
            opener=opener,
            sleep=sleep,
        )
        if imported is not True:
            raise ReconciliationError("OpenWebUI model import did not succeed") from None
        desired_ids = {model["id"] for model in desired}
        for model in all_rows:
            model_id = model.get("id")
            if not isinstance(model_id, str) or model_id in desired_ids:
                continue
            if model.get("base_model_id") is None or model.get("base_model_id") not in aliases:
                continue
            deleted = request_json(
                "POST",
                f"{base}/api/v1/models/model/delete",
                headers=auth_headers,
                payload={"id": model_id},
                opener=opener,
                sleep=sleep,
            )
            if deleted is not True:
                raise ReconciliationError(f"OpenWebUI model deletion did not succeed: {model_id}") from None
    actual = _model_list(
        request_json("GET", f"{base}/api/v1/models/export", headers=auth_headers, opener=opener, sleep=sleep),
        "model export",
    )
    verify_models(desired, actual)
    dropped = sorted(preserved_before - {str(model.get("id")) for model in actual})
    if dropped:
        raise ReconciliationError(f"model export dropped preserved rows: {', '.join(dropped)}")
    return actual


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Reconcile OpenWebUI model presets through AISIX")
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--resources", required=True)
    parser.add_argument("--env-file", required=True)
    args = parser.parse_args(argv)
    try:
        manifest = load_manifest(args.manifest)
        reconcile(args.url, manifest, Path(args.resources), Path(args.env_file))
    except (OSError, ValueError, ReconciliationError):
        print("OpenWebUI model reconciliation failed", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
