#!/usr/bin/env python3
"""Reconcile the eight OpenWebUI model presets through the AISIX router.

Reads the rendered openwebui-models-config.json (model_map, base_url,
default_models) and the mode-600 .env next to it, waits for OpenWebUI
to be ready, authenticates, and syncs the eight presets via
POST /api/v1/models/sync.

Usage:
    scripts/update-openwebui-models.py --config <config.json> [--env-file <path>] [--base-url <url>] [--dry-run]
"""

import argparse
import json
import os
import re
import sys
import time
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

PRESETS: dict[str, tuple[str, str]] = {
    "chat": ("Chat", "You are a helpful general-purpose assistant."),
    "chat_thinking": (
        "Chat (Thinking)",
        "You are a helpful assistant that thinks step by step before answering.",
    ),
    "web_research": (
        "Web Research",
        "You are a research assistant that uses web search to find current, cited information.",
    ),
    "translate_de": ("Translate to German", "Translate the user's text into German."),
    "translate_en": ("Translate to English", "Translate the user's text into English."),
    "fix_grammar_en": (
        "Fix English Grammar",
        "Fix the grammar and spelling of English text and return the corrected text.",
    ),
    "fix_grammar_de": (
        "Fix German Grammar",
        "Fix the grammar and spelling of German text and return the corrected text.",
    ),
    "linux_cli": (
        "Linux CLI",
        "You are a Linux command-line expert giving concise, correct shell commands.",
    ),
}

USER_ID = "admin"

CAPABILITY_KEYS: list[str] = [
    "file_context",
    "vision",
    "file_upload",
    "web_search",
    "image_generation",
    "code_interpreter",
    "terminal",
    "citations",
    "status_updates",
    "usage",
    "memory",
    "builtin_tools",
]

READY_TIMEOUT_SECONDS = 60
READY_INTERVAL_SECONDS = 2
RETRY_TIMEOUT_SECONDS = 60
RETRY_INTERVAL_SECONDS = 2


def aisix_display_names(content: str) -> set[str]:
    return set(re.findall(r"^\s*-\s*display_name:\s*(\S+)", content, re.M))


def read_env_file(path: str) -> dict[str, str]:
    """Parse KEY=VALUE lines from a .env file. Never prints values."""
    result: dict[str, str] = {}
    with open(path) as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            result[key.strip()] = value.strip()
    return result


def build_preset_specs(model_map: dict[str, str], default_models: list[str]) -> list[dict[str, Any]]:
    """Build the eight preset specs in the fixed default_models order."""
    specs: list[dict[str, Any]] = []
    for preset_id in default_models:
        if preset_id not in PRESETS:
            raise ValueError(f"unknown preset id {preset_id!r}")
        base_model_id = model_map.get(preset_id)
        if base_model_id is None:
            raise ValueError(f"model_map missing entry for preset {preset_id!r}")
        if base_model_id == preset_id:
            raise ValueError(f"base_model_id must differ from preset id {preset_id!r}")
        specs.append({"id": preset_id, "base_model_id": base_model_id, "name": PRESETS[preset_id][0]})
    return specs


def to_sync_model(spec: dict[str, Any], now: int, existing: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build the full ModelModel envelope for one preset."""
    preset_id = spec["id"]
    existing = existing or {}
    params: dict[str, Any] = {"system": PRESETS[preset_id][1]}
    capabilities: dict[str, bool] = dict.fromkeys(CAPABILITY_KEYS, False)
    meta: dict[str, Any] = {"capabilities": capabilities}
    if preset_id == "web_research":
        params["function_calling"] = "native"
        capabilities["web_search"] = True
        meta["defaultFeatureIds"] = ["web_search"]
        meta["builtinTools"] = {"web_search": True}
    return {
        "id": spec["id"],
        "user_id": USER_ID,
        "base_model_id": spec["base_model_id"],
        "name": spec["name"],
        "params": params,
        "meta": meta,
        "access_grants": [],
        "is_active": True,
        "updated_at": now,
        "created_at": existing.get("created_at") or now,
    }


def _request_json(
    method: str,
    url: str,
    token: str | None = None,
    payload: dict[str, Any] | None = None,
    timeout: int = 30,
) -> tuple[int, Any]:
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode()
    req = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode()
            if not body:
                return resp.status, None
            return resp.status, json.loads(body)
    except HTTPError as e:
        body = e.read().decode()
        try:
            return e.code, json.loads(body)
        except ValueError:
            return e.code, body


def _request_json_with_retry(
    method: str,
    url: str,
    token: str | None = None,
    payload: dict[str, Any] | None = None,
) -> tuple[int, Any]:
    deadline = time.monotonic() + RETRY_TIMEOUT_SECONDS
    while True:
        try:
            status, body = _request_json(method, url, token, payload)
        except (OSError, ValueError):
            status, body = 0, None
        if status == 0 or status >= 500:
            if time.monotonic() >= deadline:
                raise RuntimeError(f"request to {url} failed after {RETRY_TIMEOUT_SECONDS}s of retries")
            time.sleep(RETRY_INTERVAL_SECONDS)
            continue
        return status, body


def wait_ready(base_url: str) -> None:
    """Poll the public /ready endpoint until it returns 200."""
    deadline = time.monotonic() + READY_TIMEOUT_SECONDS
    while True:
        try:
            status, _ = _request_json("GET", f"{base_url}/ready")
            if status == 200:
                return
        except (OSError, ValueError):
            pass
        if time.monotonic() >= deadline:
            raise RuntimeError(f"{base_url}/ready did not become ready within {READY_TIMEOUT_SECONDS}s")
        time.sleep(READY_INTERVAL_SECONDS)


def authenticate(base_url: str, env: dict[str, str]) -> str:
    """Return a bearer token for the admin API."""
    status, body = _request_json_with_retry(
        "POST", f"{base_url}/api/v1/auths/signin", payload={"email": "", "password": ""}
    )
    if status == 200 and isinstance(body, dict):
        token = body.get("token")
        if isinstance(token, str) and token:
            return token
    admin_key = env.get("OPENWEBUI_API_KEY") or env.get("WEBUI_ADMIN_KEY")
    if admin_key:
        status, body = _request_json_with_retry("GET", f"{base_url}/api/v1/models/base", token=admin_key)
        if status == 200:
            return admin_key
    raise RuntimeError(
        "could not authenticate against OpenWebUI; put an OpenWebUI API key (sk-...) "
        "into OPENWEBUI_API_KEY in the .env and retry"
    )


def reconcile(
    base_url: str,
    token: str,
    model_map: dict[str, str],
    default_models: list[str],
    dry_run: bool = False,
) -> None:
    status, body = _request_json_with_retry("GET", f"{base_url}/api/v1/models/export", token=token)
    if status != 200 or not isinstance(body, list):
        raise RuntimeError(f"models export failed with status {status}")
    export_rows = [row for row in body if isinstance(row, dict)]
    now = int(time.time())
    specs = build_preset_specs(model_map, default_models)
    managed_ids = set(default_models)
    managed_rows: dict[str, Any] = {row_id: row for row in export_rows if (row_id := row.get("id")) in managed_ids}
    colliding = sorted(
        row_id
        for row_id, row in managed_rows.items()
        if row.get("base_model_id") in (None, "") or row.get("base_model_id") == row_id
    )
    if colliding:
        raise RuntimeError(
            f"preset id collides with an existing base model row: {colliding}; "
            "rename the preset or remove the base model before syncing"
        )
    models = [to_sync_model(spec, now, managed_rows.get(spec["id"])) for spec in specs]
    preserved = [row for row in export_rows if row.get("id") not in managed_ids]
    payload = {"models": preserved + models}
    if dry_run:
        print(json.dumps(payload, indent=2))
        return
    status, body = _request_json_with_retry("POST", f"{base_url}/api/v1/models/sync", token=token, payload=payload)
    if status == 200:
        if isinstance(body, list) and body:
            synced_ids = [m.get("id") for m in body if isinstance(m, dict)]
            missing = [pid for pid in default_models if pid not in synced_ids]
            if missing:
                raise RuntimeError(f"models sync did not return presets: {missing}")
        elif body == []:
            raise RuntimeError(
                "sync returned an empty model list; this indicates an internal OpenWebUI error "
                "such as a database lock, check the open-webui logs"
            )
        else:
            print("models sync returned an empty result; verifying via export")
    elif status in (404, 405, 501):
        status, body = _request_json_with_retry(
            "POST", f"{base_url}/api/v1/models/import", token=token, payload=payload
        )
        if status != 200:
            raise RuntimeError(f"models import fallback failed with status {status}")
    elif status in (401, 403, 422):
        raise RuntimeError(f"models sync rejected with status {status}")
    else:
        raise RuntimeError(f"models sync failed with status {status}")
    status, body = _request_json_with_retry("GET", f"{base_url}/api/v1/models/export", token=token)
    if status != 200 or not isinstance(body, list):
        raise RuntimeError(f"models export after sync failed with status {status}")
    exported_ids = [row.get("id") for row in body if isinstance(row, dict)]
    missing = [pid for pid in default_models if pid not in exported_ids]
    if missing:
        raise RuntimeError(f"presets missing after sync: {missing}")
    print(f"reconciled {len(default_models)} presets")


def main() -> None:
    parser = argparse.ArgumentParser(description="Reconcile OpenWebUI model presets through AISIX")
    parser.add_argument("--config", required=True, help="path to the rendered openwebui-models-config.json")
    parser.add_argument("--env-file", default=None, help="path to the .env (default: next to --config)")
    parser.add_argument(
        "--base-url", default=None, help="OpenWebUI base URL (default: from config or http://127.0.0.1:13307)"
    )
    parser.add_argument(
        "--resources", default=None, help="path to resources.yaml to verify router aliases match model_map"
    )
    parser.add_argument("--dry-run", action="store_true", help="print the sync payload without sending it")
    args = parser.parse_args()

    with open(args.config) as f:
        config = json.load(f)
    model_map = config.get("model_map")
    default_models = config.get("default_models")
    if not isinstance(model_map, dict) or not isinstance(default_models, list):
        raise RuntimeError("config must contain model_map and default_models")
    base_url = args.base_url or str(config.get("base_url") or "http://127.0.0.1:13307")
    env_path = args.env_file or os.path.join(os.path.dirname(os.path.abspath(args.config)), ".env")
    env = read_env_file(env_path)
    if args.resources:
        with open(args.resources) as f:
            alias_names = aisix_display_names(f.read())
        missing = sorted(set(model_map.values()) - alias_names)
        if missing:
            raise RuntimeError(f"model_map aliases missing from the router: {missing}")
    wait_ready(base_url)
    token = authenticate(base_url, env)
    reconcile(base_url, token, model_map, default_models, dry_run=args.dry_run)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        sys.exit(str(error))
