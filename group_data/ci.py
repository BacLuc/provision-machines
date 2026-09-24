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
    "BRAVE_API_KEY": "",
    "router_backend": "litellm",
    "router_config_path": "litellm-config.yaml",
    "openai_compatible_base_url": "http://litellm:4000/v1",
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
        "chat": "zen/deepseek-v4-flash",
        "chat_thinking": "zen/deepseek-v4-pro",
        "web_research": "zen/glm-5.3-flash",
        "translate_de": "zen/deepseek-v4-flash",
        "translate_en": "zen/deepseek-v4-flash",
        "fix_grammar_en": "zen/deepseek-v4-flash",
        "fix_grammar_de": "zen/deepseek-v4-flash",
        "linux_cli": "ollama/qwen2.5:3b",
    },
    "extra_env": {
        "ENABLE_OPENAI_API": "true",
        "OPENAI_API_BASE_URL": "http://litellm:4000/v1",
        "OPENAI_API_KEYS": "sk-litellm-local",
        "DATABASE_ENABLE_SESSION_SHARING": "true",
        "ENABLE_WEB_SEARCH": "true",
        "SEARXNG_QUERY_URL": "http://searxng:8080",
    },
    # Set in local.py — written into the rendered .env (mode 600) in compose_project_dir
    "LITELLM_MASTER_KEY": "",
    # Set in local.py — opencode/zen OpenAI-compatible API key (https://opencode.ai/zen/go/v1)
    "OPENCODE_GO_API_KEY": "",
    "OPENCODE_GO_2_API_KEY": "",
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
