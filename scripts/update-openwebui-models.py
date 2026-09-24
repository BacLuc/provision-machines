#!/usr/bin/env python3
"""Reconcile OpenWebUI model presets with the running instance.

Reads the preset definitions from the openwebui group data (rendered by
deploys/openwebui/deploy.py into openwebui-models.json) and the LiteLLM
router config, then syncs the presets into the running OpenWebUI via the
admin API. The sync is idempotent: it exports the current models first,
preserves unrelated rows, and verifies the result via a second export.

Usage:
    scripts/update-openwebui-models.py --config openwebui-models.json \
        --router-config litellm-config.yaml --env-file .env \
        --url http://127.0.0.1:13307
"""

import argparse
import json
import time
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

PRESETS: dict[str, dict[str, Any]] = {
    "chat": {
        "name": "Chat",
        "system": "You are a helpful assistant.",
        "web_search": False,
    },
    "chat_thinking": {
        "name": "Chat (Thinking)",
        "system": "You are a thoughtful assistant. Reason carefully through problems before giving your final answer.",
        "web_search": False,
    },
    "web_research": {
        "name": "Web Research",
        "system": "You are a web research assistant. Use the web search tool to find current, accurate information and cite your sources in your answer.",
        "web_search": True,
    },
    "translate_de": {
        "name": "Translate to German",
        "system": "You are a professional translator. Translate the user's text into German. Preserve the original meaning, tone, and formatting. Output only the translation.",
        "web_search": False,
    },
    "translate_en": {
        "name": "Translate to English",
        "system": "You are a professional translator. Translate the user's text into English. Preserve the original meaning, tone, and formatting. Output only the translation.",
        "web_search": False,
    },
    "fix_grammar_en": {
        "name": "Fix English Grammar",
        "system": "You are an English grammar and style editor. Correct grammar, spelling, punctuation, and style errors in the user's text. Preserve the original meaning. Output only the corrected text.",
        "web_search": False,
    },
    "fix_grammar_de": {
        "name": "Fix German Grammar",
        "system": "You are a German grammar and style editor. Correct grammar, spelling, punctuation, and style errors in the user's text. Preserve the original meaning. Output only the corrected text.",
        "web_search": False,
    },
    "linux_cli": {
        "name": "Linux CLI",
        "system": "You are a Linux command-line expert. Answer questions about Linux commands, shell scripting, and system administration. Provide concrete commands with brief explanations.",
        "web_search": False,
    },
}

# Capability keys that OpenWebUI's ModelEditor exposes; unrelated ones are
# explicitly disabled so presets do not advertise tools they do not have.
CAPABILITY_KEYS = [
    "web_search",
    "image_generation",
    "code_interpreter",
    "file_search",
    "vision",
    "audio",
    "video",
    "citations",
    "data_analysis",
    "deep_research",
    "browser_use",
    "text_to_speech",
    "speech_to_text",
    "image_input",
    "video_input",
    "audio_input",
    "input_audio",
    "output_audio",
    "function_calling",
]


def load_group_data(path: str) -> dict[str, Any]:
    with open(path) as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return data


def read_env_file(path: str) -> dict[str, str]:
    """Parse KEY=VALUE lines from a .env file. Values are never printed."""
    values: dict[str, str] = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            values[key.strip()] = value.strip()
    return values


def parse_litellm_model_names(path: str) -> list[str]:
    """Extract model_name values from the block-style litellm config YAML.

    Only supports the narrow YAML subset used by
    deploys/openwebui/files/litellm-config.yaml: block-style lists of
    mappings with scalar values. Tabs anywhere and invalid or duplicate
    model_name values are rejected.
    """
    names: list[str] = []
    seen: set[str] = set()
    with open(path) as f:
        for line in f:
            if "\t" in line:
                raise ValueError(f"Tabs are not allowed in {path}: {line!r}")
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if stripped.startswith("- "):
                stripped = stripped[2:].strip()
            if not stripped or ":" not in stripped:
                continue
            key, _, value = stripped.partition(":")
            if key != "model_name":
                continue
            name = value.strip()
            if not name or " " in name or any(c in name for c in "{}[]&*"):
                raise ValueError(f"Invalid model_name in {path}: {name!r}")
            if name in seen:
                raise ValueError(f"Duplicate model_name in {path}: {name!r}")
            seen.add(name)
            names.append(name)
    return names


def build_preset_specs(openwebui: dict[str, Any], router_names: list[str]) -> list[dict[str, Any]]:
    default_models = openwebui.get("default_models", [])
    model_map = openwebui.get("model_map", {})
    if not isinstance(default_models, list) or not isinstance(model_map, dict):
        raise ValueError("openwebui-models.json must contain default_models (list) and model_map (object)")
    specs: list[dict[str, Any]] = []
    for preset_id in default_models:
        if preset_id not in PRESETS:
            raise ValueError(f"Unknown preset id: {preset_id}")
        base_model_id = model_map.get(preset_id)
        if not isinstance(base_model_id, str) or not base_model_id:
            raise ValueError(f"Missing model_map entry for preset {preset_id}")
        if base_model_id == preset_id:
            raise ValueError(f"base_model_id must differ from the preset id: {preset_id}")
        if base_model_id not in router_names:
            raise ValueError(f"base_model_id {base_model_id} for preset {preset_id} is not in the router config")
        spec = dict(PRESETS[preset_id])
        spec["id"] = preset_id
        spec["base_model_id"] = base_model_id
        specs.append(spec)
    return specs


def to_sync_model(spec: dict[str, Any], owner: str, existing: dict[str, Any] | None) -> dict[str, Any]:
    now = int(time.time())
    if existing is not None:
        updated_at = existing.get("updated_at", now)
        created_at = existing.get("created_at", now)
    else:
        updated_at = now
        created_at = now
    web_search = bool(spec.get("web_search", False))
    capabilities: dict[str, bool] = {key: key == "web_search" and web_search for key in CAPABILITY_KEYS}
    params: dict[str, Any] = {"system": spec["system"]}
    meta: dict[str, Any] = {"capabilities": capabilities}
    if web_search:
        params["function_calling"] = "native"
        meta["defaultFeatureIds"] = ["web_search"]
        meta["builtinTools"] = {"web_search": True}
    return {
        "id": spec["id"],
        "user_id": owner,
        "base_model_id": spec["base_model_id"],
        "name": spec["name"],
        "params": params,
        "meta": meta,
        "access_grants": [],
        "is_active": True,
        "updated_at": updated_at,
        "created_at": created_at,
    }


def request_json(
    method: str,
    url: str,
    token: str | None = None,
    payload: dict[str, Any] | None = None,
    timeout: int = 30,
    retries: int = 3,
) -> tuple[int, Any]:
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode()
    req = Request(url, data=data, headers=headers, method=method)
    for attempt in range(retries + 1):
        try:
            with urlopen(req, timeout=timeout) as resp:
                body = resp.read().decode()
                if not body:
                    return resp.status, None
                return resp.status, json.loads(body)
        except HTTPError as e:
            if e.code in (503, 429) and attempt < retries:
                time.sleep(2**attempt)
                continue
            body = e.read().decode()
            try:
                return e.code, json.loads(body) if body else None
            except json.JSONDecodeError:
                return e.code, body
        except OSError:
            if attempt < retries:
                time.sleep(2**attempt)
                continue
            raise
    raise RuntimeError("unreachable")


def wait_ready(base_url: str, timeout: int = 300) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            status, _ = request_json("GET", f"{base_url}/ready", timeout=5, retries=0)
            if status == 200:
                return
        except OSError:
            pass
        time.sleep(2)
    raise TimeoutError(f"OpenWebUI at {base_url} did not become ready within {timeout}s")


def authenticate(base_url: str, env: dict[str, str]) -> tuple[str, str]:
    """Return (token, user_id) for the OpenWebUI admin API."""
    admin_key = env.get("OPENWEBUI_ADMIN_API_KEY", "")
    if admin_key:
        status, body = request_json("GET", f"{base_url}/api/v1/users/user", token=admin_key)
        if status == 200 and isinstance(body, dict) and isinstance(body.get("id"), str):
            return admin_key, body["id"]
    status, body = request_json(
        "POST",
        f"{base_url}/api/v1/auths/signin",
        payload={"email": "", "password": ""},
    )
    if status != 200:
        raise RuntimeError(
            f"Authentication failed (status {status}). "
            "Set OPENWEBUI_ADMIN_API_KEY in the openwebui .env or use a fresh database."
        )
    if not isinstance(body, dict) or not isinstance(body.get("token"), str):
        raise RuntimeError("Signin response did not contain a token")
    user_id = ""
    user = body.get("user")
    if isinstance(user, dict) and isinstance(user.get("id"), str):
        user_id = user["id"]
    return body["token"], user_id


def reconcile(
    base_url: str,
    token: str,
    owner: str,
    models: list[dict[str, Any]],
    existing: list[dict[str, Any]],
) -> None:
    existing_by_id = {m.get("id"): m for m in existing if isinstance(m, dict)}
    preset_ids = {m["id"] for m in models}
    preserved = [m for m in existing if isinstance(m, dict) and m.get("id") not in preset_ids]
    sync_models = [to_sync_model(m, owner, existing_by_id.get(m["id"])) for m in models]
    payload = {"models": sync_models + preserved}

    status, body = request_json("POST", f"{base_url}/api/v1/models/sync", token=token, payload=payload)
    if status != 200:
        if status in (404, 405, 501):
            status_import, _ = request_json(
                "POST",
                f"{base_url}/api/v1/models/import",
                token=token,
                payload=payload,
            )
            if status_import != 200:
                raise RuntimeError(f"Model import failed (status {status_import})")
        else:
            raise RuntimeError(f"Model sync failed (status {status})")
    elif isinstance(body, list) and len(body) == 0:
        raise RuntimeError("Model sync returned an empty list (sync failed)")

    status, body = request_json("GET", f"{base_url}/api/v1/models/export", token=token)
    if status != 200:
        raise RuntimeError(f"Model export failed (status {status})")
    if not isinstance(body, list):
        raise RuntimeError("Model export did not return a list")
    exported = {m.get("id"): m for m in body if isinstance(m, dict)}
    for m in sync_models:
        row = exported.get(m["id"])
        if not isinstance(row, dict) or row.get("base_model_id") != m["base_model_id"]:
            raise RuntimeError(f"Preset {m['id']} is missing or has the wrong base model after sync")


def main() -> None:
    parser = argparse.ArgumentParser(description="Reconcile OpenWebUI model presets")
    parser.add_argument("--config", required=True, help="Path to openwebui-models.json")
    parser.add_argument("--router-config", required=True, help="Path to litellm-config.yaml")
    parser.add_argument("--env-file", required=True, help="Path to the openwebui .env")
    parser.add_argument("--url", default="http://127.0.0.1:13307", help="OpenWebUI base URL")
    args = parser.parse_args()

    openwebui = load_group_data(args.config)
    router_names = parse_litellm_model_names(args.router_config)
    specs = build_preset_specs(openwebui, router_names)
    env = read_env_file(args.env_file)

    wait_ready(args.url)
    token, owner = authenticate(args.url, env)
    status, body = request_json("GET", f"{args.url}/api/v1/models/export", token=token)
    if status != 200:
        raise RuntimeError(f"Model export failed (status {status})")
    existing = body if isinstance(body, list) else []
    reconcile(args.url, token, owner, specs, existing)
    print(f"Reconciled {len(specs)} presets with OpenWebUI at {args.url}")


if __name__ == "__main__":
    main()
