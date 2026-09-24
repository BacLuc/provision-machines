#!/usr/bin/env python3
import argparse
import json
import sys
import time
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

DEFAULT_URL = "http://127.0.0.1:13307"
MAX_SYNC_ATTEMPTS = 3
SYNC_RETRY_DELAY = 5
READY_TIMEOUT = 300

PRESETS: list[dict[str, Any]] = [
    {
        "id": "chat",
        "name": "Chat",
        "system": "You are a helpful assistant. Answer concisely and accurately.",
        "tools": [],
    },
    {
        "id": "chat_thinking",
        "name": "Chat + Thinking",
        "system": "You are a helpful assistant. Think step by step before answering and show your reasoning.",
        "tools": [],
    },
    {
        "id": "web_research",
        "name": "Web Research",
        "system": "You are a research assistant. Use the web search tool to find current information, cite sources, and summarize findings.",
        "tools": ["web_search"],
    },
    {
        "id": "translate_de",
        "name": "Translate → DE",
        "system": "Translate the user's text into German. Preserve meaning, tone, and formatting. Output only the translation.",
        "tools": [],
    },
    {
        "id": "translate_en",
        "name": "Translate → EN",
        "system": "Translate the user's text into English. Preserve meaning, tone, and formatting. Output only the translation.",
        "tools": [],
    },
    {
        "id": "fix_grammar_en",
        "name": "Fix Grammar (EN)",
        "system": "Fix grammar, spelling, and punctuation in the user's English text. Keep the original meaning. Output only the corrected text.",
        "tools": [],
    },
    {
        "id": "fix_grammar_de",
        "name": "Fix Grammar (DE)",
        "system": "Fix grammar, spelling, and punctuation in the user's German text. Keep the original meaning. Output only the corrected text.",
        "tools": [],
    },
    {
        "id": "linux_cli",
        "name": "Linux CLI",
        "system": "You are a Linux CLI expert. Provide shell commands for the user's request with a one-line explanation. Prefer safe, idempotent commands.",
        "tools": [],
    },
]


def read_env_file(path: str) -> dict[str, str]:
    env: dict[str, str] = {}
    with open(path) as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            key, _, value = stripped.partition("=")
            env[key] = value
    return env


def build_preset_payloads(config: dict[str, Any]) -> list[dict[str, Any]]:
    presets_by_id = {preset["id"]: preset for preset in PRESETS}
    payloads: list[dict[str, Any]] = []
    for model_id in config["default_models"]:
        if model_id not in presets_by_id:
            sys.exit(f"unknown preset model id: {model_id}")
        preset = presets_by_id[model_id]
        payloads.append(
            {
                "id": preset["id"],
                "name": preset["name"],
                "base_model_id": config["model_map"][model_id],
                "params": {"system": preset["system"]},
                "tools": preset["tools"],
                "meta": {},
                "access_grants": [],
                "is_active": True,
                "user_id": "",
                "updated_at": int(time.time()),
                "created_at": int(time.time()),
            }
        )
    return payloads


def build_sync_payload(exported: list[dict[str, Any]], preset_payloads: list[dict[str, Any]]) -> dict[str, Any]:
    presets_by_id = {preset["id"]: preset for preset in preset_payloads}
    preserved: list[dict[str, Any]] = []
    for row in exported:
        preset = presets_by_id.get(row["id"])
        if preset is not None:
            if (
                row.get("base_model_id") != preset["base_model_id"]
                or row.get("params", {}).get("system") != preset["params"]["system"]
            ):
                sys.exit(f"exported model collides with preset id: {row['id']}")
        else:
            preserved.append(row)
    return {"models": preset_payloads + preserved}


def request_json(
    url: str,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    body: dict[str, Any] | None = None,
    timeout: int = 30,
) -> tuple[int, Any]:
    data = json.dumps(body).encode() if body is not None else None
    request_headers = dict(headers or {})
    if body is not None:
        request_headers["Content-Type"] = "application/json"
    req = Request(url, data=data, headers=request_headers, method=method)
    try:
        with urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw) if raw else None
    except HTTPError as e:
        return e.code, None
    except OSError:
        return 0, None


def authenticate(base_url: str, env: dict[str, str]) -> dict[str, str]:
    export_url = f"{base_url}/api/v1/models/export"
    status, _ = request_json(export_url)
    waited = 0
    attempt = 0
    while status == 0 and waited < READY_TIMEOUT:
        attempt += 1
        delay = min(2 * attempt, 30)
        time.sleep(delay)
        waited += delay
        status, _ = request_json(export_url)
    if status == 200:
        return {}
    if status not in (401, 403):
        sys.exit(f"unexpected status probing openwebui: {status}")
    signin_status, signin_body = request_json(
        f"{base_url}/api/v1/auths/signin",
        method="POST",
        body={"email": "", "password": ""},
    )
    if signin_status == 200 and isinstance(signin_body, dict) and signin_body.get("token"):
        return {"Authorization": f"Bearer {signin_body['token']}"}
    api_key = env.get("OPENWEBUI_ADMIN_API_KEY")
    if api_key:
        return {"Authorization": f"Bearer {api_key}"}
    sys.exit("authentication failed: set OPENWEBUI_ADMIN_API_KEY in local.py")


def verify_presets(exported: list[dict[str, Any]], preset_payloads: list[dict[str, Any]]) -> None:
    failures: list[str] = []
    exported_by_id = {row["id"]: row for row in exported}
    for preset in preset_payloads:
        row = exported_by_id.get(preset["id"])
        if row is None:
            failures.append(f"missing preset: {preset['id']}")
        elif (
            row.get("base_model_id") != preset["base_model_id"]
            or row.get("params", {}).get("system") != preset["params"]["system"]
        ):
            failures.append(f"preset mismatch: {preset['id']}")
    if failures:
        sys.exit("preset verification failed: " + "; ".join(failures))


def reconcile(base_url: str, config: dict[str, Any], env: dict[str, str], dry_run: bool = False) -> None:
    headers = authenticate(base_url, env)
    export_url = f"{base_url}/api/v1/models/export"
    status, exported = request_json(export_url, headers=headers)
    if status != 200 or not isinstance(exported, list):
        sys.exit(f"failed to export models: status {status}")
    preset_payloads = build_preset_payloads(config)
    payload = build_sync_payload(exported, preset_payloads)
    if dry_run:
        print(json.dumps(payload, indent=2))
        return
    for attempt in range(1, MAX_SYNC_ATTEMPTS + 1):
        sync_status, sync_body = request_json(
            f"{base_url}/api/v1/models/sync",
            method="POST",
            headers=headers,
            body=payload,
        )
        if sync_status == 200 and sync_body:
            break
        if sync_status == 200:
            time.sleep(SYNC_RETRY_DELAY * attempt)
            continue
        if sync_status in (404, 405, 501):
            import_status, _ = request_json(
                f"{base_url}/api/v1/models/import",
                method="POST",
                headers=headers,
                body={"models": preset_payloads},
            )
            if import_status != 200:
                sys.exit(f"model import fallback failed: status {import_status}")
            break
        sys.exit(f"model sync failed: status {sync_status}")
    status, final_export = request_json(export_url, headers=headers)
    if status != 200 or not isinstance(final_export, list):
        sys.exit(f"failed to re-export models: status {status}")
    verify_presets(final_export, preset_payloads)


def main() -> None:
    parser = argparse.ArgumentParser(description="Reconcile OpenWebUI models")
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--config", required=True)
    parser.add_argument("--env-file", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    with open(args.config) as f:
        config = json.load(f)
    env = read_env_file(args.env_file) if args.env_file else {}
    reconcile(args.url, config, env, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
