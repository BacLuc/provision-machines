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
        "chat_thinking": "router-chat_thinking",
        "web_research": "router-web_research",
        "translate_de": "router-translate_de",
        "translate_en": "router-translate_en",
        "fix_grammar_en": "router-fix_grammar_en",
        "fix_grammar_de": "router-fix_grammar_de",
        "linux_cli": "router-linux_cli",
    },
    "extra_env": {
        "ENABLE_OPENAI_API": "true",
        "OPENAI_API_BASE_URL": "http://aisix:3000/v1",
        "OPENAI_API_KEYS": "${OPENWEBUI_CALLER_KEY}",
        "DEFAULT_MODELS": "router-chat,router-chat_thinking,router-web_research,router-translate_de,router-translate_en,router-fix_grammar_en,router-fix_grammar_de,router-linux_cli",
        "ENABLE_MODEL_FILTER": "true",
        "MODEL_FILTER_LIST": "router-chat,router-chat_thinking,router-web_research,router-translate_de,router-translate_en,router-fix_grammar_en,router-fix_grammar_de,router-linux_cli",
    },
    "zen": {
        "base_url": "https://opencode.ai/zen/go/v1",
        "models": {
            "chat": "glm-5.3-flash",
            "chat_thinking": "glm-5.3",
            "web_research": "deepseek-v4-pro",
            "translate": "glm-5.3-flash",
            "grammar": "glm-5.3-flash",
            "linux_cli": "deepseek-v4-flash",
        },
    },
    "ollama": {
        "base_url": "http://host.docker.internal:11434/v1",
        "models": {
            "chat": "qwen2.5:3b",
            "chat_thinking": "qwen2.5:3b",
            "web_research": "qwen2.5:3b",
            "translate": "qwen2.5:3b",
            "grammar": "qwen2.5:3b",
            "linux_cli": "qwen2.5:3b",
        },
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
