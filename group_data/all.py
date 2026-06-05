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

vshn_tools = {"enabled": False}

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
    "enabled": False,
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
    "ssh_config_paths_to_include": [],
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

devcontainer_cli = {
    "enabled": True,
}

displaylink_driver = {
    "enabled": False,
}

firefox = {
    "enabled": True,
}

flatpak = {
    "enabled": True,
}

flatpaks: list[str] = []

fluxcd = {
    "enabled": False,
}

fzf = {
    "enabled": False,
}

git_lfs = {
    "enabled": False,
    # renovate: datasource=github-releases depName=git-lfs/git-lfs
    "git_lfs_version": "3.7.1",
    "git_lfs_checksum": "1c0b6ee5200ca708c5cebebb18fdeb0e1c98f1af5c1a9cba205a4c0ab5a5ec08",
}

gnome = {
    "enable_customize_gnome": False,
}

nvm = {
    "_sudo_for_global_install": False,
    # renovate: datasource=github-releases depName=nvm-sh/nvm
    "nvm_version": "v0.40.5",
    "enabled": True,
}

kubectl = {
    "enabled": False,
    # renovate: datasource=github-releases depName=itaysk/kubectl-neat
    "kubectl_neat_version": "2.0.4",
    # renovate: datasource=github-releases depName=robscott/kube-capacity
    "kubectl_capacity_version": "0.8.0",
    # renovate: datasource=github-releases depName=rajatjindal/kubectl-modify-secret
    "kubectl_modify_secret_version": "0.0.47",
    "enable_oidc_plugin": False,
}

tmux = {
    "enabled": False,
}

nvim = {
    "enabled": False,
}

lazygit = {
    "enabled": False,
    # renovate: datasource=github-releases depName=jesseduffield/lazygit
    "lazygit_version": "0.61.1",
    "lazygit_checksum": "5c7c81884167cf38561c82704ec8783bcd199f484e6c63c781783f4f5a662a2a",
}

ollama = {
    "enabled": False,
    # renovate: datasource=github-releases depName=ollama/ollama
    "ollama_version": "0.20.3",
    "model": "qwen2.5:3b",
}

homebrew = {
    "enabled": False,
}

snap = {
    "enabled": False,
    "refresh": {
        "timer": "4:00-9:00",
    },
}

snaps: list[str] = []

classic_snaps: list[str] = []

sysctl = {
    "enabled": False,
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
    "enabled": False,
    "enable_helm_support": True,
    "enable_memory_monitor": True,
    "memory_monitor_limit_gb": 10,
    "memory_monitor_cron_frequency": "*/5 * * * *",
}

vifm = {
    "enabled": False,
}

jetbrains = {
    "enabled": False,
}

okular = {
    "enabled": False,
}

ubuntu_desktop = {
    "enabled": False,
    "enable_dependencies": True,
    "enable_favorite_apps": True,
    "enable_keyboard_layouts": True,
    "enable_shortcuts": True,
    "enable_gpaste_config": False,
    "enable_testing_browser_desktop": False,
    "favorite_apps": [
        {"desktop_file_name": "Alacritty.desktop", "shortcut": "<Super>z"},
        {"desktop_file_name": "firefox_firefox.desktop", "shortcut": "<Super>u"},
        {"desktop_file_name": "phpstorm_phpstorm.desktop", "shortcut": "<Super>i"},
        {"desktop_file_name": "dev.zed.Zed.desktop", "shortcut": "<Super>o"},
        {"desktop_file_name": "gitclient.desktop", "shortcut": "<Super>g"},
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
    "enabled": False,
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
