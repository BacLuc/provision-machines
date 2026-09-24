#!/usr/bin/env python3
"""Reconcile the OpenWebUI model presets with the running instance.

Reads the preset definitions from openwebui-models.json and the router
aliases from aisix-resources.yaml, then syncs them into OpenWebUI via
POST /api/v1/models/sync. Idempotent: a second run produces no changes.
"""

import argparse
import json
import re
import time
from typing import Any, cast
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

PRESETS: dict[str, dict[str, Any]] = {
    "chat": {
        "name": "Chat",
        "web_search": False,
        "system": "You are a helpful assistant.",
    },
    "chat_thinking": {
        "name": "Chat (Thinking)",
        "web_search": False,
        "system": "You are a helpful assistant that reasons carefully before answering.",
    },
    "web_research": {
        "name": "Web Research",
        "web_search": True,
        "system": (
            "You are a research assistant. Use web search to find current, accurate information and cite your sources."
        ),
    },
    "translate_de": {
        "name": "Translate to German",
        "web_search": False,
        "system": (
            "Translate the user's text into German. Preserve the original meaning, tone, "
            "and formatting. Reply with only the translation."
        ),
    },
    "translate_en": {
        "name": "Translate to English",
        "web_search": False,
        "system": (
            "Translate the user's text into English. Preserve the original meaning, tone, "
            "and formatting. Reply with only the translation."
        ),
    },
    "fix_grammar_en": {
        "name": "Fix English Grammar",
        "web_search": False,
        "system": (
            "Fix the grammar, spelling, and style of the user's English text. Preserve the "
            "original meaning. Reply with only the corrected text."
        ),
    },
    "fix_grammar_de": {
        "name": "Fix German Grammar",
        "web_search": False,
        "system": (
            "Fix the grammar, spelling, and style of the user's German text. Preserve the "
            "original meaning. Reply with only the corrected text."
        ),
    },
    "linux_cli": {
        "name": "Linux CLI",
        "web_search": False,
        "system": (
            "You are a Linux command-line expert. Answer with concrete shell commands and explain them briefly."
        ),
    },
}

RETRY_STATUSES = (503, 429)
MAX_RETRIES = 5
READY_TIMEOUT = 300.0


def load_config(models_path: str, resources_path: str) -> tuple[dict[str, Any], list[str]]:
    with open(models_path) as f:
        openwebui = cast(dict[str, Any], json.load(f))
    return openwebui, parse_aisix_model_names(resources_path)


def read_env_file(path: str) -> dict[str, str]:
    env: dict[str, str] = {}
    with open(path) as f:
        for lineno, raw in enumerate(f, start=1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                raise ValueError(f"{path}:{lineno}: expected KEY=VALUE")
            key, value = line.split("=", 1)
            env[key.strip()] = value.strip()
    return env


def parse_aisix_model_names(path: str) -> list[str]:
    with open(path) as f:
        lines = f.read().splitlines()

    display_names: list[str] = []
    seen_keys: set[str] = set()
    in_models = False
    for lineno, raw in enumerate(lines, start=1):
        if "\t" in raw:
            raise ValueError(f"{path}:{lineno}: tabs are not supported")
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "&" in stripped or "*" in stripped:
            raise ValueError(f"{path}:{lineno}: anchors and aliases are not supported")
        if re.search(r"[\[\]{}]", re.sub(r"\$\{[^}]*\}", "", stripped)):
            raise ValueError(f"{path}:{lineno}: flow style is not supported")
        indent = len(raw) - len(raw.lstrip(" "))
        if indent % 2 != 0:
            raise ValueError(f"{path}:{lineno}: indentation must be a multiple of 2 spaces")
        if indent == 0:
            key = stripped.split(":", 1)[0].strip().strip('"')
            if key in seen_keys:
                raise ValueError(f"{path}:{lineno}: duplicate key {key}")
            seen_keys.add(key)
            if key == "_format_version":
                value = stripped.split(":", 1)[1].strip()
                if value != '"1"':
                    raise ValueError(f'{path}:{lineno}: _format_version must be "1"')
            in_models = key == "models"
            continue
        if in_models and indent == 2 and stripped.startswith("- display_name:"):
            name = stripped.split(":", 1)[1].strip().strip('"')
            if not name.startswith("router-"):
                continue
            if name in display_names:
                raise ValueError(f"{path}:{lineno}: duplicate display_name {name}")
            display_names.append(name)
    if "_format_version" not in seen_keys:
        raise ValueError(f'{path}: missing _format_version: "1"')
    return display_names


def build_preset_specs(openwebui: dict[str, Any]) -> list[dict[str, Any]]:
    model_map = cast(dict[str, str], openwebui["model_map"])
    specs: list[dict[str, Any]] = []
    for preset_id in cast(list[str], openwebui["default_models"]):
        base_model_id = model_map[preset_id]
        if base_model_id == preset_id:
            raise ValueError(f"preset id {preset_id} collides with its router alias")
        preset = PRESETS[preset_id]
        specs.append(
            {
                "id": preset_id,
                "base_model_id": base_model_id,
                "name": preset["name"],
                "system": preset["system"],
                "web_search": preset["web_search"],
            }
        )
    return specs


def to_sync_model(spec: dict[str, Any], owner: str, existing: dict[str, dict[str, Any]]) -> dict[str, Any]:
    now = int(time.time())
    prev = existing.get(spec["id"])
    capabilities = {
        "vision": False,
        "citations": False,
        "usage": False,
        "web_search": bool(spec["web_search"]),
        "code_interpreter": False,
        "image_generation": False,
        "audio": False,
        "video": False,
        "file_search": False,
        "function_calling": False,
        "mcp": False,
        "chat": True,
    }
    meta: dict[str, Any] = {"capabilities": capabilities}
    params: dict[str, Any] = {"system": spec["system"]}
    if spec["web_search"]:
        meta["defaultFeatureIds"] = ["web_search"]
        meta["builtinTools"] = {"web_search": True}
        params["function_calling"] = "native"
    return {
        "id": spec["id"],
        "user_id": owner,
        "base_model_id": spec["base_model_id"],
        "name": spec["name"],
        "params": params,
        "meta": meta,
        "access_grants": [],
        "is_active": True,
        "updated_at": int(prev["updated_at"]) if prev and "updated_at" in prev else now,
        "created_at": int(prev["created_at"]) if prev and "created_at" in prev else now,
    }


def _base_model_id(row: dict[str, Any]) -> Any:
    info = row.get("info")
    if isinstance(info, dict) and "base_model_id" in info:
        return info["base_model_id"]
    return row.get("base_model_id")


def normalize_preserved(row: dict[str, Any], owner: str) -> dict[str, Any]:
    now = int(time.time())
    info = row.get("info")
    source = info if isinstance(info, dict) else row
    return {
        "id": source.get("id") or row["id"],
        "user_id": source.get("user_id") or owner,
        "base_model_id": source.get("base_model_id"),
        "name": source.get("name") or row.get("name"),
        "params": source.get("params", {}),
        "meta": source.get("meta", {}),
        "access_grants": source.get("access_grants", []),
        "is_active": source.get("is_active", True),
        "updated_at": int(source["updated_at"]) if "updated_at" in source else now,
        "created_at": int(source["created_at"]) if "created_at" in source else now,
    }


def request_json(
    method: str,
    url: str,
    token: str | None = None,
    payload: dict[str, Any] | None = None,
    retries: int = MAX_RETRIES,
) -> tuple[int, Any]:
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode()
    for attempt in range(retries + 1):
        req = Request(url, data=data, headers=headers, method=method)
        try:
            with urlopen(req, timeout=30) as resp:
                body = resp.read().decode()
                return resp.status, json.loads(body) if body else None
        except HTTPError as e:
            if e.code in RETRY_STATUSES and attempt < retries:
                time.sleep(min(2**attempt, 30))
                continue
            body = e.read().decode()
            try:
                return e.code, json.loads(body) if body else None
            except json.JSONDecodeError:
                return e.code, body
        except URLError:
            if attempt < retries:
                time.sleep(min(2**attempt, 30))
                continue
            raise
    raise AssertionError("unreachable")


def wait_ready(base_url: str, timeout: float = READY_TIMEOUT) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urlopen(f"{base_url}/ready", timeout=5) as resp:
                if resp.status == 200:
                    return
        except (HTTPError, URLError):
            pass
        time.sleep(2)
    raise RuntimeError(f"{base_url}/ready did not return 200 within {timeout:.0f}s")


def authenticate(base_url: str, env: dict[str, str]) -> tuple[str, str]:
    admin_key = env.get("OPENWEBUI_ADMIN_API_KEY", "")
    if admin_key:
        status, data = request_json("GET", f"{base_url}/api/v1/users/user", token=admin_key)
        if status != 200:
            raise RuntimeError(
                f"admin key rejected by {base_url} (HTTP {status}); set OPENWEBUI_ADMIN_API_KEY in the .env file"
            )
        return admin_key, str(data["id"])
    status, data = request_json("POST", f"{base_url}/api/v1/auths/signin", payload={"email": "", "password": ""})
    if status != 200:
        raise RuntimeError(f"signin failed (HTTP {status}); set OPENWEBUI_ADMIN_API_KEY in the .env file")
    return str(data["token"]), str(data["id"])


def _as_model_list(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return cast(list[dict[str, Any]], data)
    if isinstance(data, dict) and isinstance(data.get("data"), list):
        return cast(list[dict[str, Any]], data["data"])
    raise RuntimeError(f"unexpected API response shape: {type(data).__name__}")


def reconcile(
    base_url: str,
    token: str,
    owner: str,
    specs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    status, data = request_json("GET", f"{base_url}/api/v1/models", token=token)
    if status != 200:
        raise RuntimeError(f"export failed (HTTP {status}); is OpenWebUI reachable at {base_url}?")
    existing = _as_model_list(data)
    by_id = {row["id"]: row for row in existing}
    for spec in specs:
        prev = by_id.get(spec["id"])
        if prev is not None and _base_model_id(prev) != spec["base_model_id"]:
            raise RuntimeError(
                f"model {spec['id']} exists with base_model_id {_base_model_id(prev)!r}, "
                f"expected {spec['base_model_id']!r}"
            )
    models = [to_sync_model(spec, owner, by_id) for spec in specs]
    preserved = [normalize_preserved(row, owner) for row in existing if row["id"] not in {s["id"] for s in specs}]
    payload = {"models": models + preserved}
    status, data = request_json("POST", f"{base_url}/api/v1/models/sync", token=token, payload=payload)
    if status in (404, 405, 501):
        status, _ = request_json("POST", f"{base_url}/api/v1/models/import", token=token, payload={"models": models})
        if status != 200:
            raise RuntimeError(f"import failed (HTTP {status})")
        print("sync endpoint unavailable; imported presets via /models/import (non-exact)")
    elif status != 200:
        raise RuntimeError(f"sync failed (HTTP {status})")
    elif data == []:
        raise RuntimeError(
            "sync returned an empty model list; this indicates an internal OpenWebUI error "
            "such as a database lock, check the open-webui logs"
        )
    status, data = request_json("GET", f"{base_url}/api/v1/models", token=token)
    if status != 200:
        raise RuntimeError(f"re-export failed (HTTP {status})")
    exported = _as_model_list(data)
    by_id = {row["id"]: row for row in exported}
    for spec in specs:
        row = by_id.get(spec["id"])
        if row is None or _base_model_id(row) != spec["base_model_id"]:
            raise RuntimeError(f"preset {spec['id']} missing or wrong base_model_id after sync")
    return exported


def main() -> None:
    parser = argparse.ArgumentParser(description="Reconcile OpenWebUI model presets")
    parser.add_argument("--url", default="http://127.0.0.1:13307", help="OpenWebUI base URL")
    parser.add_argument("--models", required=True, help="path to openwebui-models.json")
    parser.add_argument("--resources", required=True, help="path to aisix-resources.yaml")
    parser.add_argument("--env", required=True, help="path to the .env file")
    args = parser.parse_args()

    openwebui, router_aliases = load_config(args.models, args.resources)
    expected_aliases = set(cast(list[str], openwebui["model_map"].values()))
    if set(router_aliases) != expected_aliases:
        raise SystemExit(f"aisix-resources.yaml lists {sorted(router_aliases)}, expected {sorted(expected_aliases)}")
    specs = build_preset_specs(openwebui)
    env = read_env_file(args.env)
    wait_ready(args.url)
    token, owner = authenticate(args.url, env)
    reconcile(args.url, token, owner, specs)
    print(f"reconciled {len(specs)} presets")


if __name__ == "__main__":
    main()
