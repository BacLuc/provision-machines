import os

ai_agent_devcontainer = {"enabled": True}

alacritty = {
    "enabled": True,
    "font_size": 12,
}

python = {
    "enabled": True,
    "uv": {
        "enabled": True,
    },
}

vshn_tools = {"enabled": True}

basicsetup = {
    "additional_tools": [
        "ansible-lint",
        "apt-transport-https",
        "bat",
        "build-essential",
        "clang",
        "cloc",
        # "chromium-browser",
        # "chromium-codecs-ffmpeg",
        # "chromium-browser-l18n",
        "cmake",
        "curl",
        "git",
        "graphviz",
        # "gpaste2",
        # "gnome-tweaks",
        # "nextcloud-desktop",
        "jq",
        "libglu1-mesa",
        "libgtk-3-dev",
        "libstdc++-12-dev",
        "net-tools",
        "ninja-build",
        "ocrmypdf",
        "pkg-config",
        "procps",
        "tig",
        "xz-utils",
        "yamllint",
    ],
    "basic_tools": [
        "dos2unix",
        "fd-find",
        # "firefox",
        "htop",
        "nano",
        "rsync",
        "tar",
        "tree",
        "unzip",
        "wget",
        "zip",
    ],
    "enabled": True,
    "locale": "en_US.UTF-8",
    "timezone": "Europe/Zurich",
}

docker = {
    "enabled": True,
    "daemon_config_folder": "/etc/docker",
    "provision_daemon_json": False,
}

backup_burp = {
    "enabled": False,
    "ppa": "ppa:vshn/backup",
    "ppa_list_filename": "vshn-ubuntu-backup-noble.sources",
    "secret_store_app_name": "burp",
    "secret_store_local_pw_instance": "personal-laptop-instance",
    "secret_store_server_instance": "personal-server-laptop-server",
}

bash = {
    "enabled": True,
}

shell_includes = {
    "enabled": False,
}

zsh = {
    "enabled": True,
    "enable_zsh_autosuggestions": False,
    "completions_dir": "/home/{user}/zsh/completions",
    "motd_path": "/etc/profile.d/update-motd.sh",
}

basic_utils = {
    "enabled": True,
    "enable_direnv": True,
    "enable_flutter": False,
    "enable_keepassxc": False,
    "enable_signal": False,
    "enable_java": True,
    "enable_ssh_config_dir": True,
    "ssh_config_paths_to_include": ["./config.d/*"],
    "enable_openvpn_config_import_network_manager": True,
    "enable_zoom": False,
    "enable_go": False,
    "ssh_key": {
        "enable": True,
        "filename": "id_ed25519",
    },
    "ssh_agent": {
        "enable": True,
    },
    "gcr_ssh_agent": {
        "enable": False,
    },
    "python": {
        "venvs": [],
    },
}

cleanup_scripts = {
    "enabled": True,
    "dir": "/usr/local/bin/cleanup_scripts.d",
}

update_packages_script = {
    "dir": "/usr/local/bin/update-script.d",
}

auto_provision = {
    "enabled": False,
    "on_calendar": "Sun *-*-* 02:00:00",
    "notify_on_calendar": "Sun *-*-* 00:00:00",
    "checkout_dir": "/home/{user}/provision-machines",
    "branch": "main",
    "state_dir": "/var/lib/auto-provision",
}

devcontainer_cli = {
    "enabled": True,
}

displaylink_driver = {
    "enabled": True,
}

charging_state_monitor = {
    "enabled": False,
}

firefox = {
    "enabled": True,
}

firefox_taskbar_tabs = {
    "enabled": True,
    "tabs": {
        "teams": {
            "enabled": False,
            "name": "Teams",
            "url": "https://teams.microsoft.com/",
            "tab_id": "5b4e9bd5-8cd1-47ea-8945-66f73dd85fe8",
        },
        "jira": {
            "enabled": False,
            "name": "Jira",
            "url": "https://vshnticket.atlassian.net/",
            "tab_id": "05c3722e-4f98-4056-910b-d15d58628b22",
        },
        "customer-service-board": {
            "enabled": False,
            "name": "Customer Service Board",
            "url": "https://vshnticket.atlassian.net/jira/software/c/projects/VSHNOPS/boards/95?quickFilter=660",
            "tab_id": "35699144-8592-4b92-8806-4a651d52b1f4",
            "keywords": ["customer board", "cs board", "CS Board", "customer", "cs", "service board", "board"],
        },
        "confluence": {
            "enabled": False,
            "name": "Confluence",
            "url": "https://vshnwiki.atlassian.net/",
            "tab_id": "40b8fc34-4f39-4a3a-927b-98eb493aed1a",
        },
        "vshn-gitlab": {
            "enabled": False,
            "name": "VSHN GitLab",
            "url": "https://git.vshn.net/",
            "tab_id": "44f1788e-8889-4097-8d8d-da60a1c68a06",
        },
        "zoom": {
            "enabled": False,
            "name": "Zoom",
            "url": "https://vshn.zoom.us",
            "url_prefixes": ["https://vshn.zoom.us/j/"],
            "tab_id": "235345df-e0f8-4875-9d5b-22afdac2f956",
        },
        "rocket-chat": {
            "enabled": False,
            "name": "RocketChat",
            "url": "https://vshn.chat",
            "tab_id": "0f35f5e3-a0da-454d-a334-e319bea4ed4d",
        },
        "github": {
            "enabled": False,
            "name": "GitHub",
            "url": "https://github.com/",
            "tab_id": "cb08b72e-f725-4922-9d98-71ec3c2e741c",
        },
        "google-meet": {
            "enabled": False,
            "name": "Google Meet",
            "url": "https://meet.google.com/",
            "tab_id": "d993bcb9-751f-4add-9194-ddcab64bf700",
        },
        "allquiet": {
            "enabled": False,
            "name": "AllQuiet",
            "url": "https://allquiet.eu/app",
            "tab_id": "b119239c-fbd1-45ee-8350-1a89bf262460",
        },
    },
}

flatpak = {
    "enabled": True,
}

flatpaks: list[str] = []

fluxcd = {
    "enabled": False,
}

fzf = {
    "enabled": True,
}

git_lfs = {
    "enabled": True,
    # renovate: datasource=github-releases depName=git-lfs/git-lfs
    "git_lfs_version": "3.7.1",
    "git_lfs_checksum": "6b92b05c4588b4a5373b2b4102dbb302757d8ec6671da67cf9e4f9ccb01cd349",
}

github_cli = {
    "enabled": True,
}

gnome = {
    "enable_customize_gnome": False,
}

nvm = {
    "_sudo_for_global_install": False,
    # renovate: datasource=github-releases depName=nvm-sh/nvm
    "nvm_version": "v0.41.0",
    "enabled": True,
}

kubectl = {
    "enabled": True,
    # renovate: datasource=github-releases depName=itaysk/kubectl-neat
    "kubectl_neat_version": "2.0.4",
    # renovate: datasource=github-releases depName=robscott/kube-capacity
    "kubectl_capacity_version": "0.8.0",
    # renovate: datasource=github-releases depName=rajatjindal/kubectl-modify-secret
    "kubectl_modify_secret_version": "0.0.47",
    "enable_oidc_plugin": False,
}

tmux = {
    "enabled": True,
}

nvim = {
    "enabled": True,
}

lazygit = {
    "enabled": True,
    # renovate: datasource=github-releases depName=jesseduffield/lazygit
    "lazygit_version": "0.65.1",
    "lazygit_checksum": "971bc18be3ddd75f67462016eeda9bc5581644f90e5e961ec11b450ef60be894",
}

syft = {
    "enabled": True,
}

ollama = {
    "enabled": False,
    # renovate: datasource=github-releases depName=ollama/ollama
    "ollama_version": "0.32.5",
    "model": "qwen2.5:3b",
}

t3_code = {
    "enabled": False,
}

ask_ai = {
    "enabled": True,
    "endpoint": "https://router.requesty.ai/v1",
    "model": "novita/deepseek/deepseek-v3.2",
    # Set in local.py — written directly into ~/.config/aichat/config.yaml (mode 600)
    "api_key": "",
}

homebrew = {
    "enabled": True,
}

snap = {
    "enabled": True,
    "refresh": {
        "timer": "4:00-9:00",
    },
}

snaps: list[str] = []

classic_snaps: list[str] = []

sysctl = {
    "enabled": True,
    "settings": {
        "fs.inotify.max_queued_events": 1048576,
        "fs.inotify.max_user_instances": 1048576,
        "fs.inotify.max_user_watches": 1048576,
    },
}

motd = {
    "enable_disk_usage": False,
}

zed = {
    "enabled": True,
    "enable_helm_support": True,
    "enable_memory_monitor": True,
    "memory_monitor_limit_gb": 10,
    "memory_monitor_cron_frequency": "*/5 * * * *",
}

vifm = {
    "enabled": True,
}

jetbrains = {
    "enabled": False,
}

okular = {
    "enabled": True,
}

ubuntu_desktop = {
    "enabled": True,
    "enable_dependencies": True,
    "enable_favorite_apps": True,
    "enable_keyboard_layouts": True,
    "enable_shortcuts": True,
    "enable_gpaste_config": False,
    "enable_testing_browser_desktop": False,
    "favorite_apps": [
        {"desktop_file_name": "Alacritty.desktop", "shortcut": "<Super>y"},
        {"desktop_file_name": "firefox_firefox.desktop", "shortcut": "<Super>x"},
        {"desktop_file_name": "phpstorm_phpstorm.desktop", "shortcut": "<Super>r"},
        {"desktop_file_name": "dev.zed.Zed.desktop", "shortcut": "<Super>f"},
        {"desktop_file_name": "org.mozilla.Thunderbird.desktop", "shortcut": "<Super><Alt>c"},
    ],
}

hashicorp_apt_repo = {
    "enabled": False,
}

hashicorp_vault_cli = {
    "enabled": False,
}

php_development = {
    "enabled": False,
    # renovate: datasource=github-tags depName=php/php-src
    "php_version": "8.4.10",
}

openwebui = {
    "enabled": True,
    "BRAVE_API_KEY": "",
    "extra_env": {
        "ENABLE_OPENAI_API": "true",
        "OPENAI_API_BASE_URL": "http://aisix:3000/v1",
        "DEFAULT_MODELS": "chat,chat_thinking,web_research,translate_de,translate_en,fix_grammar_en,fix_grammar_de,linux_cli",
        "ENABLE_API_KEYS": "true",
    },
    # Set in local.py — written into the openwebui .env (mode 600)
    "opencode_api_key": "",
    "opencode_api_key_2": "",
    "opencode_api_key_3": "",
    "requesty_api_key": "",
    "cortecs_api_key": "",
    "openwebui_caller_key": "",
    "opencode_base_url": "https://opencode.ai/zen/go/v1",
    "requesty_base_url": "https://router.requesty.ai/v1",
    "cortecs_base_url": "https://api.cortecs.ai/v1",
    "zen_model_chat": "deepseek-v4-flash",
    "zen_model_chat_thinking": "deepseek-v4-pro",
    "zen_model_web_research": "qwen3.8-flash",
    "zen_model_fast": "mimo-v2.6-flash",
    "requesty_model_chat": "novita/deepseek/deepseek-v3.2",
    "cortecs_model_chat": "glm-5.3-flash",
}

vagrant = {
    "enabled": False,
}

ubuntu_cleanup = {
    "enabled": True,
}


def __load_local_overrides(override_file: str) -> None:
    import importlib.util

    def _deep_merge(base: dict, override: dict) -> dict:  # type: ignore[type-arg]
        result = dict(base)
        for k, v in override.items():
            if k in result and isinstance(result[k], dict) and isinstance(v, dict):
                result[k] = _deep_merge(result[k], v)
            else:
                result[k] = v
        return result

    local_path = os.path.join(os.path.dirname(str(__file__)), override_file)
    if not os.path.exists(local_path):
        return

    spec = importlib.util.spec_from_file_location("_local_overrides", local_path)
    if spec is None or spec.loader is None:
        return
    local_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(local_mod)

    g = globals()
    for key in [k for k in vars(local_mod) if not k.startswith("_")]:
        val = getattr(local_mod, key)
        if key in g and isinstance(g[key], dict) and isinstance(val, dict):
            g[key] = _deep_merge(g[key], val)
        else:
            g[key] = val


if os.getenv("CI"):
    __load_local_overrides("ci.py")
__load_local_overrides("local.py")
