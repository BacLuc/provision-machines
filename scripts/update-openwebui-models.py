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
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

PRESET_NAMES: dict[str, str] = {
    "chat": "Chat",
    "chat_thinking": "Chat (Thinking)",
    "web_research": "Web Research",
    "translate_de": "Translate to German",
    "translate_en": "Translate to English",
    "fix_grammar_en": "Fix English Grammar",
    "fix_grammar_de": "Fix German Grammar",
    "linux_cli": "Linux CLI",
}

READY_TIMEOUT_SECONDS = 60
READY_INTERVAL_SECONDS = 2
RETRY_TIMEOUT_SECONDS = 60
RETRY_INTERVAL_SECONDS = 2


class YamlParseError(ValueError):
    pass


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


def _strip_comment(line: str) -> str:
    in_quote = False
    for i, ch in enumerate(line):
        if ch == '"':
            in_quote = not in_quote
        elif ch == "#" and not in_quote and (i == 0 or line[i - 1].isspace()):
            return line[:i]
    return line


def _indent_of(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _parse_scalar(text: str) -> Any:
    text = text.strip()
    if not text:
        return None
    if len(text) >= 2 and text.startswith('"') and text.endswith('"'):
        return text[1:-1]
    if text == "true":
        return True
    if text == "false":
        return False
    if text == "null":
        return None
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        pass
    return text


def _split_key_value(text: str) -> tuple[str, str]:
    if ":" not in text:
        raise YamlParseError(f"expected ':' in {text!r}")
    key, value = text.split(":", 1)
    return key.strip(), value.strip()


class _BlockParser:
    """Narrow block-style YAML parser for the AISIX resources file shape."""

    def __init__(self, lines: list[str]) -> None:
        self.lines = lines
        self.index = 0

    def parse(self) -> Any:
        value = self._parse_block(0)
        if self.index != len(self.lines):
            raise YamlParseError("unexpected content after top-level block")
        return value

    def _parse_block(self, indent: int) -> Any:
        if self.index >= len(self.lines):
            return None
        line = self.lines[self.index]
        if _indent_of(line) < indent:
            return None
        if line.lstrip().startswith("- "):
            return self._parse_sequence(indent)
        return self._parse_mapping(indent)

    def _parse_mapping(self, indent: int) -> dict[str, Any]:
        result: dict[str, Any] = {}
        while self.index < len(self.lines):
            line = self.lines[self.index]
            line_indent = _indent_of(line)
            if line_indent < indent:
                break
            if line_indent > indent:
                raise YamlParseError("unexpected indentation")
            stripped = line.lstrip()
            if stripped.startswith("- "):
                break
            key, value_text = _split_key_value(stripped)
            if key in result:
                raise YamlParseError(f"duplicate key {key!r}")
            self.index += 1
            if value_text:
                result[key] = _parse_scalar(value_text)
            else:
                result[key] = self._parse_block(indent + 2)
        return result

    def _parse_sequence(self, indent: int) -> list[Any]:
        items: list[Any] = []
        while self.index < len(self.lines):
            line = self.lines[self.index]
            line_indent = _indent_of(line)
            if line_indent < indent:
                break
            if line_indent > indent:
                raise YamlParseError("unexpected indentation")
            stripped = line.lstrip()
            if not stripped.startswith("- "):
                break
            rest = stripped[2:]
            self.index += 1
            if not rest:
                items.append(self._parse_block(indent + 2))
            elif ":" in rest:
                key, value_text = _split_key_value(rest)
                item: dict[str, Any] = {}
                if key in item:
                    raise YamlParseError(f"duplicate key {key!r}")
                if value_text:
                    item[key] = _parse_scalar(value_text)
                else:
                    item[key] = self._parse_block(indent + 4)
                while self.index < len(self.lines):
                    nxt = self.lines[self.index]
                    nxt_indent = _indent_of(nxt)
                    if nxt_indent < indent + 2:
                        break
                    if nxt_indent > indent + 2:
                        raise YamlParseError("unexpected indentation")
                    nxt_stripped = nxt.lstrip()
                    if nxt_stripped.startswith("- "):
                        break
                    k2, v2 = _split_key_value(nxt_stripped)
                    if k2 in item:
                        raise YamlParseError(f"duplicate key {k2!r}")
                    self.index += 1
                    if v2:
                        item[k2] = _parse_scalar(v2)
                    else:
                        item[k2] = self._parse_block(indent + 4)
                items.append(item)
            else:
                items.append(_parse_scalar(rest))
        return items


def parse_aisix_model_names(content: str) -> list[tuple[str, list[str]]]:
    """Return ordered (display_name, [target model names]) for routing models.

    Rejects tabs, flow-style brackets, and duplicate keys at the same
    level. Never returns or logs provider/API secret values.
    """
    lines: list[str] = []
    for raw in content.splitlines():
        if "\t" in raw:
            raise YamlParseError("tabs are not supported")
        line = _strip_comment(raw).rstrip()
        if not line.strip():
            continue
        no_interp = re.sub(r"\$\{[^}]*\}", "", line)
        if "[" in no_interp or "{" in no_interp:
            raise YamlParseError("flow style is not supported")
        lines.append(line)
    tree = _BlockParser(lines).parse()
    if not isinstance(tree, dict):
        raise YamlParseError("top level must be a mapping")
    models = tree.get("models")
    if not isinstance(models, list):
        raise YamlParseError("missing models list")
    result: list[tuple[str, list[str]]] = []
    for model in models:
        if not isinstance(model, dict):
            raise YamlParseError("model entry must be a mapping")
        routing = model.get("routing")
        if not isinstance(routing, dict):
            continue
        display_name = model.get("display_name")
        if not isinstance(display_name, str):
            raise YamlParseError("routing model missing display_name")
        targets = routing.get("targets")
        if not isinstance(targets, list):
            raise YamlParseError(f"routing model {display_name!r} missing targets")
        target_names: list[str] = []
        for target in targets:
            if not isinstance(target, dict):
                raise YamlParseError("routing target must be a mapping")
            name = target.get("model")
            if not isinstance(name, str):
                raise YamlParseError(f"routing target of {display_name!r} missing model")
            target_names.append(name)
        result.append((display_name, target_names))
    return result


def build_preset_specs(model_map: dict[str, str], default_models: list[str]) -> list[dict[str, Any]]:
    """Build the eight preset specs in the fixed default_models order."""
    specs: list[dict[str, Any]] = []
    for preset_id in default_models:
        if preset_id not in PRESET_NAMES:
            raise ValueError(f"unknown preset id {preset_id!r}")
        base_model_id = model_map.get(preset_id)
        if base_model_id is None:
            raise ValueError(f"model_map missing entry for preset {preset_id!r}")
        if base_model_id == preset_id:
            raise ValueError(f"base_model_id must differ from preset id {preset_id!r}")
        specs.append({"id": preset_id, "base_model_id": base_model_id, "name": PRESET_NAMES[preset_id]})
    return specs


def to_sync_model(spec: dict[str, Any], user_id: str, now: int) -> dict[str, Any]:
    """Build the full ModelModel envelope for one preset."""
    params: dict[str, Any] = {}
    meta: dict[str, Any] = {}
    if spec["id"] == "web_research":
        params = {"function_calling": "native"}
        meta = {
            "capabilities": {"web_search": True},
            "defaultFeatureIds": ["web_search"],
            "builtinTools": {"web_search": True},
        }
    return {
        "id": spec["id"],
        "user_id": user_id,
        "base_model_id": spec["base_model_id"],
        "name": spec["name"],
        "params": params,
        "meta": meta,
        "access_grants": [],
        "is_active": True,
        "updated_at": now,
        "created_at": now,
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
        except URLError:
            status, body = 0, None
        if status == 0 or (isinstance(status, int) and status >= 500):
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
        except URLError:
            pass
        if time.monotonic() >= deadline:
            raise RuntimeError(f"{base_url}/ready did not become ready within {READY_TIMEOUT_SECONDS}s")
        time.sleep(READY_INTERVAL_SECONDS)


def authenticate(base_url: str, env: dict[str, str]) -> tuple[str, dict[str, Any] | None]:
    """Return (bearer token, signin body) for the admin API."""
    status, body = _request_json_with_retry(
        "POST", f"{base_url}/api/v1/auths/signin", payload={"email": "", "password": ""}
    )
    if status == 200 and isinstance(body, dict):
        token = body.get("token")
        if isinstance(token, str) and token:
            return token, body
    admin_key = env.get("OPENWEBUI_API_KEY") or env.get("WEBUI_ADMIN_KEY")
    if admin_key:
        status, body = _request_json_with_retry("GET", f"{base_url}/api/v1/users/user", token=admin_key)
        if status == 200:
            return admin_key, None
    raise RuntimeError(
        "could not authenticate against OpenWebUI; set OPENWEBUI_API_KEY or WEBUI_ADMIN_KEY "
        "in the .env (or configure an admin user) and retry"
    )


def _get_user_id(export_rows: list[dict[str, Any]], signin_body: dict[str, Any] | None) -> str:
    for row in export_rows:
        user_id = row.get("user_id")
        if isinstance(user_id, str) and user_id:
            return user_id
    if signin_body is not None:
        user_id = signin_body.get("id")
        if isinstance(user_id, str) and user_id:
            return user_id
    return "admin"


def reconcile(
    base_url: str,
    token: str,
    signin_body: dict[str, Any] | None,
    model_map: dict[str, str],
    default_models: list[str],
    dry_run: bool = False,
) -> None:
    status, body = _request_json_with_retry("GET", f"{base_url}/api/v1/models/export", token=token)
    if status != 200 or not isinstance(body, list):
        raise RuntimeError(f"models export failed with status {status}")
    export_rows = [row for row in body if isinstance(row, dict)]
    user_id = _get_user_id(export_rows, signin_body)
    now = int(time.time())
    specs = build_preset_specs(model_map, default_models)
    models = [to_sync_model(spec, user_id, now) for spec in specs]
    payload = {"models": models}
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
        "--resources", default=None, help="path to aisix-resources.yaml to verify router aliases match model_map"
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
            aliases = parse_aisix_model_names(f.read())
        alias_names = {name for name, _ in aliases}
        expected = set(model_map.values())
        if alias_names != expected:
            raise RuntimeError(f"router aliases {sorted(alias_names)} do not match model_map {sorted(expected)}")
    wait_ready(base_url)
    token, signin_body = authenticate(base_url, env)
    reconcile(base_url, token, signin_body, model_map, default_models, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
