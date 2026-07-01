#!/usr/bin/env python3
"""Update VSHN US AI models in the opencode config.

Fetches the model list from us-ai.corp.vshn.net and updates the
us-ai provider section in the opencode.json config file.

Usage:
    scripts/update-us-ai-models.py                  # Update with one model per price class
    scripts/update-us-ai-models.py --all            # Include all non-preset models
    scripts/update-us-ai-models.py --list            # List available models without updating
    scripts/update-us-ai-models.py --price-class byusage  # Only models from a specific price class
"""

import argparse
import getpass
import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

API_BASE_URL = "https://us-ai.corp.vshn.net/api/v1"
CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "deploys",
    "development_tools",
    "ai_agent_devcontainer",
    "files",
    "opencode",
    "opencode.json",
)
PROVIDER_NAME = "vshn-us-ai"

# Price class prefixes, in order of preference for the "one per class" default
PRICE_CLASSES = [
    "byusage",
    "subscription",
    "expensive",
    "openrouter",
]

# Self-created/preset model IDs that are agent wrappers, not raw models
PRESET_MODEL_IDS = {
    "coding-api",
    "fix-english-grammar",
    "fix-german-grammar",
    "linux-command-line",
    "text-summary",
    "translate-to-english",
    "translate-to-german",
    "vshn-handbook-and-kb",
    "web-research",
    "chat",
    "chat--thinking",
    "create-or-edit-confluence-page",
}

# Preferred model per price class (model_id -> display name suffix)
PREFERRED_MODELS = {
    "byusage": "byusage.nebius/deepseek-ai/DeepSeek-V3.2",
    "subscription": "subscription.glm-5.2",
    "expensive": "expensive.gemini-3-flash",
    "openrouter": "openrouter.deepseek/deepseek-chat-v3.1",
}

# Extra models to always include regardless of price class filtering
EXTRA_MODELS = {
    "-claude-haiku-v45": "Claude Haiku 4.5 (preset)",
    "-claude-sonnet-v46": "Claude Sonnet 4.6 (preset)",
    "expensive.gpt-5.3-codex": "GPT-5.3 Codex (expensive)",
    "expensive.gpt-5.5": "GPT-5.5 (expensive)",
}


def fetch_models(api_key=None, base_url=None):
    """Fetch model list from the US AI API."""
    url = (base_url or API_BASE_URL) + "/models"
    headers = {"Accept": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    req = Request(url, headers=headers)
    try:
        with urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
    except HTTPError as e:
        print(f"HTTP error fetching models: {e.code} {e.reason}", file=sys.stderr)
        sys.exit(1)
    except URLError as e:
        print(f"Network error fetching models: {e.reason}", file=sys.stderr)
        print(f"Hint: Make sure you can reach {url}", file=sys.stderr)
        sys.exit(1)

    # The API may return {"data": [...]} or just a list
    if isinstance(data, dict) and "data" in data:
        return data["data"]
    if isinstance(data, list):
        return data
    print(f"Unexpected API response format: {type(data)}", file=sys.stderr)
    sys.exit(1)


def get_display_name(model):
    """Get a human-readable display name for a model."""
    model_id = model.get("id", "")
    name = model.get("name", "")

    # Use pre-configured display name for extra models
    if model_id in EXTRA_MODELS:
        return EXTRA_MODELS[model_id]

    # Use the name from the API if it differs from the id
    if not name or name == model_id:
        name = model_id

    # Add price class hint in parentheses for clarity
    prefix = get_price_class(model_id)
    if prefix:
        short_name = name if name != model_id else model_id.split("/")[-1].split(".")[-1]
        return f"{short_name} ({prefix})"

    return name if name != model_id else model_id


def get_price_class(model_id):
    """Extract the price class prefix from a model ID."""
    for prefix in PRICE_CLASSES:
        if model_id.startswith(prefix + "."):
            return prefix
    # Check for prefix with slash (openrouter style)
    for prefix in PRICE_CLASSES:
        if model_id.startswith(prefix + "/"):
            return prefix
    return None


def is_preset(model_id, model=None):
    """Check if a model is a self-created preset/agent wrapper."""
    # Extra models are always included, never treated as presets
    if model_id in EXTRA_MODELS:
        return False
    if model_id in PRESET_MODEL_IDS:
        return True
    # Also detect presets from the API response
    if model and model.get("preset", False):
        return True
    # Models with dash prefix are presets
    if model_id.startswith("-"):
        return True
    return False


def filter_models(models, mode="default", price_class=None):
    """Filter models based on mode and optional price class.

    Args:
        models: List of model dicts from API
        mode: 'default' (one per price class + extras), 'all' (all non-preset),
              or 'list' (just for display)
        price_class: Optional specific price class to filter to
    """
    # Filter out preset/agent models
    available = []
    for model in models:
        model_id = model.get("id", "")
        if is_preset(model_id, model):
            continue
        available.append(model)

    # Filter by specific price class if requested
    if price_class:
        available = [m for m in available if get_price_class(m.get("id", "")) == price_class]

    if mode == "all" or mode == "list":
        return available

    # Default mode: one model per price class + extras
    result = []
    picked_ids = set()

    # First prefer the configured preferred models if they exist
    for prefix, preferred_id in PREFERRED_MODELS.items():
        if price_class and prefix != price_class:
            continue
        for model in available:
            if model.get("id") == preferred_id:
                result.append(model)
                picked_ids.add(preferred_id)
                break

    # Then fill in any price class that didn't have a preferred model available
    seen_classes = {get_price_class(m.get("id", "")) for m in result}
    for model in available:
        model_id = model.get("id", "")
        if model_id in picked_ids:
            continue
        pc = get_price_class(model_id)
        if pc and pc not in seen_classes:
            result.append(model)
            picked_ids.add(model_id)
            seen_classes.add(pc)

    # Always include extra models (Anthropic, GPT, etc.) if available
    for model in available:
        model_id = model.get("id", "")
        if model_id in EXTRA_MODELS and model_id not in picked_ids:
            result.append(model)
            picked_ids.add(model_id)

    return result


def update_config(models, config_path, npm_package=None, provider_name=None, api_base_url=None):
    """Update the opencode.json config with the given models."""
    with open(config_path) as f:
        config = json.load(f)

    provider_name = provider_name or PROVIDER_NAME
    api_base_url = api_base_url or API_BASE_URL

    models_dict = {}
    for model in models:
        model_id = model.get("id", "")
        display_name = get_display_name(model)
        models_dict[model_id] = {"name": display_name}

    # Sort models by key for deterministic output
    sorted_models = dict(sorted(models_dict.items()))

    provider_config = {
        "npm": npm_package or "@ai-sdk/openai-compatible",
        "name": "VSHN US AI",
        "models": sorted_models,
    }

    config["provider"][provider_name] = provider_config

    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
        f.write("\n")

    print(f"Updated {len(sorted_models)} models in {config_path}")


def list_models(models):
    """Prettyprint the available models grouped by price class."""
    by_class = {}
    presets = []

    for model in models:
        model_id = model.get("id", "")
        name = model.get("name", model_id)
        pc = get_price_class(model_id)
        if is_preset(model_id, model):
            presets.append(model)
        elif pc:
            by_class.setdefault(pc, []).append((model_id, name))
        else:
            by_class.setdefault("other", []).append((model_id, name))

    for prefix in PRICE_CLASSES:
        if prefix in by_class:
            print(f"\n  {prefix.upper()}:")
            for mid, name in sorted(by_class[prefix]):
                print(f"    {mid:50s}  →  {name}")

    if "other" in by_class:
        print("\n  OTHER:")
        for mid, name in sorted(by_class["other"]):
            print(f"    {mid:50s}  →  {name}")

    if presets:
        print("\n  PRESETS (excluded by default):")
        for model in presets:
            mid = model.get("id", "")
            name = model.get("name", mid)
            print(f"    {mid:50s}  →  {name}")


def main():
    parser = argparse.ArgumentParser(description="Update VSHN US AI models in opencode config")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Include all non-preset models (not just one per price class)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available models without updating config",
    )
    parser.add_argument(
        "--price-class",
        choices=PRICE_CLASSES,
        help="Only include models from a specific price class",
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("US_AI_API_KEY"),
        help="API key for authentication (or set US_AI_API_KEY env var)",
    )
    parser.add_argument(
        "--api-base-url",
        default=API_BASE_URL,
        help=f"API base URL (default: {API_BASE_URL})",
    )
    parser.add_argument(
        "--config-path",
        default=CONFIG_PATH,
        help=f"Path to opencode.json (default: {CONFIG_PATH})",
    )

    args = parser.parse_args()

    # Resolve API key: CLI flag > env var > prompt
    api_key = args.api_key or os.environ.get("US_AI_API_KEY")
    if not api_key:
        api_key = getpass.getpass("US AI API key: ")

    # Fetch models from API
    models = fetch_models(api_key=api_key, base_url=args.api_base_url)

    # Determine mode
    if args.list:
        mode = "list"
    elif args.all:
        mode = "all"
    else:
        mode = "default"

    # Filter models
    filtered = filter_models(models, mode=mode, price_class=args.price_class)

    if args.list:
        list_models(models)
        print(f"\n  {len(filtered)} model(s) would be included in '{mode}' mode")
        return

    # Show what will be updated
    print("Models to include:")
    for model in filtered:
        model_id = model.get("id", "")
        print(f"  {model_id}  →  {get_display_name(model)}")

    # Update config
    update_config(
        filtered,
        config_path=args.config_path,
        api_base_url=args.api_base_url,
    )


if __name__ == "__main__":
    main()
