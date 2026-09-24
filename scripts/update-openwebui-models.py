#!/usr/bin/env python3
"""Reconcile OpenWebUI model presets through the LiteLLM router."""

import argparse
import json
import os
import re
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

_MAX_ATTEMPTS = 5
_BACKOFF_SECONDS = 1

PRESETS: dict[str, tuple[str, str, bool]] = {
    "chat": ("Chat", "You are a helpful assistant.", False),
    "chat_thinking": ("Chat (Thinking)", "You are a helpful assistant. Think step by step before answering.", False),
    "web_research": (
        "Web Research",
        "You are a research assistant. Use the web search tool to find current information before answering.",
        True,
    ),
    "translate_de": ("Translate to German", "Translate the user's text into natural German.", False),
    "translate_en": ("Translate to English", "Translate the user's text into natural English.", False),
    "fix_grammar_en": (
        "Fix English Grammar",
        "Fix the grammar and spelling of the user's English text without changing its meaning.",
        False,
    ),
    "fix_grammar_de": (
        "Fix German Grammar",
        "Fix the grammar and spelling of the user's German text without changing its meaning.",
        False,
    ),
    "linux_cli": (
        "Linux CLI",
        "You are a Linux command line expert. Answer with concise, copy-pasteable shell commands.",
        False,
    ),
}

_CAPABILITY_KEYS = [
    "vision",
    "citations",
    "file_search",
    "function_calling",
    "web_search",
    "supports_web_search",
    "supports_vision",
    "supports_citations",
    "supports_file_search",
    "supports_function_calling",
]


class YamlParseError(ValueError):
    pass


def read_env_file(path: str) -> dict[str, str]:
    result: dict[str, str] = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            result[key.strip()] = value.strip()
    return result


def _parse_scalar(value: str) -> Any:
    if value in ("true", "True"):
        return True
    if value in ("false", "False"):
        return False
    if value in ("null", "None", "~"):
        return None
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    return value


def _tokenize(text: str) -> list[tuple[int, str]]:
    entries: list[tuple[int, str]] = []
    for line in text.splitlines():
        if "\t" in line:
            raise YamlParseError("tabs are not supported")
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if " #" in stripped:
            stripped = stripped.split(" #", 1)[0].rstrip()
            if not stripped:
                continue
        if any(c in stripped for c in "&*"):
            raise YamlParseError("anchors are not supported")
        if any(c in stripped for c in "{}[]"):
            raise YamlParseError("flow style is not supported")
        entries.append((len(line) - len(line.lstrip(" ")), stripped))
    return entries


def _parse_mapping(entries: list[tuple[int, str]], pos: int, indent: int) -> tuple[dict[str, Any], int]:
    result: dict[str, Any] = {}
    while pos < len(entries):
        cur_indent, content = entries[pos]
        if cur_indent < indent:
            break
        if cur_indent > indent:
            raise YamlParseError(f"malformed indentation: {content}")
        if content.startswith("- "):
            break
        if ":" not in content:
            raise YamlParseError(f"expected key: value, got: {content}")
        key, _, value = content.partition(":")
        key = key.strip()
        if not key:
            raise YamlParseError(f"empty key: {content}")
        if key in result:
            raise YamlParseError(f"duplicate key: {key}")
        value = value.strip()
        if value == "":
            if pos + 1 < len(entries) and entries[pos + 1][0] > indent:
                child, pos = _parse_block(entries, pos + 1, entries[pos + 1][0])
                result[key] = child
            else:
                result[key] = None
        else:
            result[key] = _parse_scalar(value)
            pos += 1
    return result, pos


def _parse_sequence(entries: list[tuple[int, str]], pos: int, indent: int) -> tuple[list[Any], int]:
    result: list[Any] = []
    while pos < len(entries):
        cur_indent, content = entries[pos]
        if cur_indent < indent:
            break
        if cur_indent > indent:
            raise YamlParseError(f"malformed indentation: {content}")
        if not content.startswith("- "):
            break
        item = content[2:].strip()
        if item == "":
            if pos + 1 < len(entries) and entries[pos + 1][0] > indent:
                child, pos = _parse_block(entries, pos + 1, entries[pos + 1][0])
                result.append(child)
            else:
                result.append(None)
        elif ":" in item:
            key, _, value = item.partition(":")
            key = key.strip()
            value = value.strip()
            mapping: dict[str, Any] = {}
            if value == "":
                if pos + 1 < len(entries) and entries[pos + 1][0] > indent:
                    child, pos = _parse_block(entries, pos + 1, entries[pos + 1][0])
                    mapping[key] = child
                else:
                    mapping[key] = None
            else:
                mapping[key] = _parse_scalar(value)
                pos += 1
            if pos < len(entries) and entries[pos][0] > indent:
                child, pos = _parse_mapping(entries, pos, entries[pos][0])
                for k, v in child.items():
                    if k in mapping:
                        raise YamlParseError(f"duplicate key: {k}")
                    mapping[k] = v
            result.append(mapping)
        else:
            result.append(_parse_scalar(item))
            pos += 1
    return result, pos


def _parse_block(entries: list[tuple[int, str]], pos: int, indent: int) -> tuple[Any, int]:
    if pos >= len(entries):
        return None, pos
    cur_indent, content = entries[pos]
    if cur_indent < indent:
        return None, pos
    if cur_indent > indent:
        raise YamlParseError(f"malformed indentation: {content}")
    if content.startswith("- "):
        return _parse_sequence(entries, pos, indent)
    if ":" in content:
        return _parse_mapping(entries, pos, indent)
    raise YamlParseError(f"unsupported line: {content}")


def _parse_yaml(text: str) -> dict[str, Any]:
    entries = _tokenize(text)
    if not entries:
        return {}
    value, pos = _parse_block(entries, 0, entries[0][0])
    if pos != len(entries):
        raise YamlParseError("unexpected content after top-level block")
    if not isinstance(value, dict):
        raise YamlParseError("top-level block must be a mapping")
    return value


def parse_litellm_model_names(text: str) -> list[str]:
    root = _parse_yaml(text)
    model_list = root.get("model_list")
    if not isinstance(model_list, list):
        raise YamlParseError("missing model_list sequence")
    names: list[str] = []
    for entry in model_list:
        if not isinstance(entry, dict) or not isinstance(entry.get("model_name"), str):
            raise YamlParseError("model_list entries must be mappings with a model_name string")
        names.append(entry["model_name"])
    return names


def build_preset_specs(models: list[dict[str, str]]) -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    for model in models:
        preset_id = model["preset_id"]
        router_model_id = model["router_model_id"]
        if router_model_id == preset_id:
            raise ValueError(f"router_model_id must differ from preset_id: {preset_id}")
        if preset_id not in PRESETS:
            raise ValueError(f"unknown preset_id: {preset_id}")
        name, prompt, web_search = PRESETS[preset_id]
        specs.append(
            {
                "preset_id": preset_id,
                "router_model_id": router_model_id,
                "name": name,
                "prompt": prompt,
                "web_search": web_search,
            }
        )
    return specs


def _capabilities(web_search: bool) -> dict[str, bool]:
    return {key: key in ("web_search", "supports_web_search") and web_search for key in _CAPABILITY_KEYS}


def to_sync_model(
    spec: dict[str, Any], admin_user_id: str, existing: dict[str, dict[str, Any]], now: int
) -> dict[str, dict[str, Any]]:
    preset_id = spec["preset_id"]
    router_model_id = spec["router_model_id"]
    web_search = spec["web_search"]
    existing_row = existing.get(preset_id)
    updated_at = existing_row["updated_at"] if existing_row else now
    created_at = existing_row["created_at"] if existing_row else now
    params: dict[str, Any] = {"system": spec["prompt"]}
    if web_search:
        params["function_calling"] = "native"
    meta: dict[str, Any] = {
        "profile_image_url": None,
        "description": None,
        "capabilities": _capabilities(web_search),
        "defaultFeatureIds": ["web_search"] if web_search else [],
        "builtinTools": {"web_search": True} if web_search else {},
    }
    preset_row: dict[str, Any] = {
        "id": preset_id,
        "user_id": admin_user_id,
        "base_model_id": router_model_id,
        "name": spec["name"],
        "params": params,
        "meta": meta,
        "access_grants": [],
        "is_active": True,
        "updated_at": updated_at,
        "created_at": created_at,
    }
    base_row: dict[str, Any] = {
        "id": router_model_id,
        "user_id": admin_user_id,
        "base_model_id": None,
        "name": router_model_id,
        "params": {},
        "meta": {
            "profile_image_url": None,
            "description": None,
            "capabilities": _capabilities(False),
            "defaultFeatureIds": [],
            "builtinTools": {},
        },
        "access_grants": [],
        "is_active": True,
        "updated_at": updated_at,
        "created_at": created_at,
    }
    return {"preset": preset_row, "base": base_row}


def normalize_preserved(row: dict[str, Any], owner: str) -> dict[str, Any]:
    info = row.get("info")
    if not isinstance(info, dict):
        info = {}
    now = int(time.time())
    return {
        "id": row["id"],
        "user_id": row.get("user_id") or owner,
        "base_model_id": row.get("base_model_id") or info.get("base_model_id"),
        "name": row.get("name") or "",
        "params": info.get("params") or row.get("params") or {},
        "meta": info.get("meta") or row.get("meta") or {},
        "access_grants": row.get("access_grants") or [],
        "is_active": bool(row.get("is_active", True)),
        "updated_at": int(row.get("updated_at") or info.get("updated_at") or now),
        "created_at": int(row.get("created_at") or info.get("created_at") or now),
    }


def request_json(method: str, url: str, token: str, payload: dict[str, Any] | None = None) -> Any:
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = None
    if payload is not None:
        data = json.dumps(payload).encode()
        headers["Content-Type"] = "application/json"
    req = Request(url, data=data, headers=headers, method=method)
    for attempt in range(_MAX_ATTEMPTS):
        try:
            with urlopen(req, timeout=30) as resp:
                body = resp.read().decode()
                return json.loads(body) if body else None
        except HTTPError as e:
            if e.code in (503, 429) and attempt < _MAX_ATTEMPTS - 1:
                time.sleep(_BACKOFF_SECONDS * (2**attempt))
                continue
            raise
        except URLError:
            if attempt < _MAX_ATTEMPTS - 1:
                time.sleep(_BACKOFF_SECONDS * (2**attempt))
                continue
            raise
    raise RuntimeError("unreachable")


def wait_ready(base_url: str, timeout: int = 300) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urlopen(f"{base_url}/api/ready", timeout=5) as resp:
                if resp.status == 200:
                    return
        except OSError:
            pass
        time.sleep(5)
    raise RuntimeError(f"OpenWebUI not ready after {timeout}s")


def _admin_user_id(base_url: str, token: str) -> str:
    response = request_json("GET", f"{base_url}/api/v1/users/", token)
    if not isinstance(response, dict) or not isinstance(response.get("users"), list):
        raise RuntimeError("could not determine admin user id")
    for user in response["users"]:
        if not isinstance(user, dict) or user.get("role") != "admin":
            continue
        user_id = user.get("id")
        if isinstance(user_id, str):
            return user_id
    raise RuntimeError("could not determine admin user id")


def authenticate(args: argparse.Namespace, env: dict[str, str]) -> str:
    admin_key = str(args.admin_api_key) or env.get("OPENWEBUI_ADMIN_API_KEY", "")
    if admin_key:
        try:
            _admin_user_id(args.base_url, admin_key)
            return admin_key
        except (HTTPError, URLError):
            pass
    try:
        response = request_json("POST", f"{args.base_url}/api/v1/auths/signin", "", {"email": "", "password": ""})
    except (HTTPError, URLError) as e:
        raise RuntimeError("no admin API key available; set OPENWEBUI_ADMIN_API_KEY in local.py") from e
    if not isinstance(response, dict):
        raise RuntimeError("signin did not return a token; set OPENWEBUI_ADMIN_API_KEY in local.py")
    token = response.get("token")
    if not isinstance(token, str) or not token:
        raise RuntimeError("signin did not return a token; set OPENWEBUI_ADMIN_API_KEY in local.py")
    return token


def reconcile(args: argparse.Namespace, token: str) -> None:
    exported = request_json("GET", f"{args.base_url}/api/v1/models/export", token)
    if not isinstance(exported, list):
        raise RuntimeError("unexpected export response")
    existing: dict[str, dict[str, Any]] = {}
    for row in exported:
        if isinstance(row, dict) and isinstance(row.get("id"), str):
            existing[row["id"]] = row
    now = int(time.time())
    admin_user_id = _admin_user_id(args.base_url, token)
    specs = build_preset_specs(args.models)
    managed_ids: set[str] = set()
    payload: list[dict[str, Any]] = []
    for spec in specs:
        rows = to_sync_model(spec, admin_user_id, existing, now)
        payload.append(rows["preset"])
        payload.append(rows["base"])
        managed_ids.add(spec["preset_id"])
        managed_ids.add(spec["router_model_id"])
    for row in exported:
        if isinstance(row, dict) and row.get("id") not in managed_ids:
            payload.append(normalize_preserved(row, admin_user_id))
    body = {"models": payload}
    if args.dry_run:
        print(json.dumps(body, indent=2))
        return
    try:
        response = request_json("POST", f"{args.base_url}/api/v1/models/sync", token, body)
    except HTTPError as e:
        if e.code not in (404, 405, 501):
            raise
        for row in payload:
            request_json("POST", f"{args.base_url}/api/v1/models/import", token, {"models": [row]})
        return
    if not isinstance(response, list) or not response:
        raise RuntimeError("sync returned an empty result; models were not reconciled")
    present = {row.get("id") for row in response if isinstance(row, dict)}
    missing = managed_ids - present
    if missing:
        raise RuntimeError(f"sync did not create models: {sorted(missing)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Reconcile OpenWebUI model presets through the LiteLLM router")
    parser.add_argument(
        "--args-file", required=True, help="JSON file with base_url, admin_api_key, config_path and models"
    )
    parser.add_argument("--dry-run", action="store_true", help="print the sync payload without posting")
    args = parser.parse_args()
    with open(args.args_file) as f:
        data = json.load(f)
    base_url = str(data["base_url"])
    admin_api_key = str(data.get("admin_api_key", ""))
    config_path = str(data["config_path"])
    models = data["models"]
    env = read_env_file(os.path.join(os.path.dirname(config_path), ".env"))
    config_router_ids = set(parse_litellm_model_names(Path(config_path).read_text()))
    args_router_ids = {str(model["router_model_id"]) for model in models}
    if config_router_ids != args_router_ids:
        raise RuntimeError(
            f"router_model_id mismatch: litellm config has {sorted(config_router_ids)}, args file has {sorted(args_router_ids)}"
        )
    namespace = argparse.Namespace(base_url=base_url, admin_api_key=admin_api_key, models=models, dry_run=args.dry_run)
    wait_ready(base_url)
    token = authenticate(namespace, env)
    reconcile(namespace, token)


if __name__ == "__main__":
    main()
