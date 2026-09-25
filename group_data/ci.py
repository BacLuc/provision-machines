vshn_tools = {"enabled": True}

basicsetup = {
    "enabled": True,
}

docker = {
    "enabled": True,
    "provision_daemon_json": True,
}

bash = {
    "enabled": True,
}

shell_includes = {
    "enabled": True,
}

zsh = {
    "enabled": False,
}

basic_utils = {
    "enable_go": True,
    "python": {
        "venvs": ["test-env"],
    },
}

flatpaks: list[str] = []

fluxcd = {
    "enabled": True,
}

fzf = {
    "enabled": True,
}

git_lfs = {
    "enabled": True,
}

kubectl = {
    "enabled": False,
    "enable_oidc_plugin": True,
}

nvm = {
    "_sudo_for_global_install": True,
}

tmux = {
    "enabled": True,
}

nvim = {
    "enabled": False,
}

lazygit = {
    "enabled": True,
}

ollama = {
    "enabled": False,
}

t3_code = {
    "enabled": True,
}

homebrew = {
    "enabled": True,
}

snap = {
    "enabled": False,
}

snaps: list[str] = []

sysctl = {
    "enabled": True,
}

motd = {
    "enable_disk_usage": True,
}

vifm = {
    "enabled": True,
}

jetbrains = {
    "enabled": True,
}

okular = {
    "enabled": True,
}

zed = {
    "enabled": False,
}

hashicorp_apt_repo = {
    "enabled": False,
}

hashicorp_vault_cli = {
    "enabled": False,
}

openwebui = {
    "enabled": False,
    # Set in local.py — the Brave Search API key for SearXNG.
    "BRAVE_API_KEY": "",
    # Set in local.py — the OpenCode Go API key for the Zen OpenAI-compatible endpoint.
    "OPENCODE_GO_API_KEY": "",
    # Set in local.py — the AISIX caller key (also used by OpenWebUI to call the proxy).
    "OPENWEBUI_CALLER_KEY": "",
    # Set in local.py — the OpenWebUI admin API key used by the model reconcile script.
    "OPENWEBUI_ADMIN_API_KEY": "",
    "router_backend": "aisix",
    "router_config_path": "aisix-resources.yaml",
    "openai_compatible_base_url": "http://aisix:3000/v1",
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
        "chat": "router-chat",
        "chat_thinking": "router-chat-thinking",
        "web_research": "router-web-research",
        "translate_de": "router-translate-de",
        "translate_en": "router-translate-en",
        "fix_grammar_en": "router-fix-grammar-en",
        "fix_grammar_de": "router-fix-grammar-de",
        "linux_cli": "router-linux-cli",
    },
    "extra_env": {
        "ENABLE_OPENAI_API": "true",
        "OPENAI_API_BASE_URL": "${OPENAI_COMPATIBLE_BASE_URL}",
        "OPENAI_API_KEYS": "${OPENWEBUI_CALLER_KEY}",
        "DEFAULT_MODELS": "chat,chat_thinking,web_research,translate_de,translate_en,fix_grammar_en,fix_grammar_de,linux_cli",
        "ENABLE_MODEL_FILTER": "true",
        "MODEL_FILTER_LIST": "chat,chat_thinking,web_research,translate_de,translate_en,fix_grammar_en,fix_grammar_de,linux_cli",
    },
    "zen": {
        "base_url": "https://opencode.ai/zen/go/v1",
        "models": {
            "chat": "deepseek-v4-flash",
            "chat_thinking": "deepseek-v4-pro",
            "web_research": "qwen3.8-max",
            "translate": "glm-5.2",
            "fix_grammar": "deepseek-v4-flash",
            "linux_cli": "deepseek-v4-pro",
        },
    },
    "ollama": {
        "base_url": "http://host.docker.internal:11434/v1",
        "model": "qwen2.5:3b",
    },
}

vagrant = {
    "enabled": False,
}

ubuntu_cleanup = {
    "enabled": True,
}

ubuntu_desktop = {
    "enabled": False,
}

displaylink_driver = {
    "enabled": False,
}

charging_state_monitor = {
    "enabled": False,
}
