ai_agent_devcontainer = {
    "enabled": True
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
        "cmake",
        "curl",
        "git",
        "graphviz",
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
    "provision_daemon_json": True,
}

alacritty = {
    "enabled": True,
    "font_size": 12,
}

backup_burp = {
    "enabled": False,
}

bash = {
    "enabled": True,
}

zsh = {
    "enabled": True,
}

basic_utils = {
    "enabled": True,
}

cleanup_scripts = {
    "enabled": True,
    "dir": "/usr/local/bin/cleanup_scripts.d",
}

devcontainer_cli = {
    "enabled": True,
}

displaylink_driver = {
    "enabled": False,
}

firefox = {
    "enabled": False,
}

flatpak = {
    "enabled": True,
}

fluxcd = {
    "enabled": False,
}

fzf = {
    "enabled": False,
}

git_lfs = {
    "enabled": False,
}

gnome = {
    "enable_customize_gnome": False,
}

nvm = {
    # renovate: datasource=github-releases depName=nvm-sh/nvm
    "nvm_version": "v0.40.4",
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

enable_nvim = False

enable_lazygit = False

lazygit = {
    # renovate: datasource=github-releases depName=jesseduffield/lazygit
    "lazygit_version": "0.61.1",
    "lazygit_checksum": "5c7c81884167cf38561c82704ec8783bcd199f484e6c63c781783f4f5a662a2a",
}

enable_ollama = False

ollama = {
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

enable_sysctl = False

sysctl = {
    "settings": {
        "fs.inotify.max_queued_events": 1048576,
        "fs.inotify.max_user_instances": 1048576,
        "fs.inotify.max_user_watches": 1048576,
    },
}

motd = {
    "enable_disk_usage": False,
}

enable_alacritty = False

alacritty = {
    "font_size": 12,
}

enable_firefox = False

firefox = {
    "enabled": False,
}

enable_zed = False

zed = {
    "enable_helm_support": True,
    "enable_memory_monitor": True,
    "memory_monitor_limit_gb": 10,
    "memory_monitor_cron_frequency": "*/5 * * * *",
}

enable_vifm = False

enable_jetbrains = False

okular = {
    "enabled": False,
}

enable_ubuntu_desktop = True

ubuntu_desktop = {
    "enable_dependencies": True,
    "enable_favorite_apps": True,
    "enable_keyboard_layouts": True,
    "enable_shortcuts": True,
    "enable_gpaste_config": False,
    "enable_testing_browser_desktop": False,
}

hashicorp_apt_repo = {
    "enabled": False,
}

enable_hashicorp_vault_cli = False

enable_php_development = False

php_development = {
    # renovate: datasource=github-tags depName=php/php-src
    "php_version": "8.4.10",
}

enable_openwebui = False

openwebui_compose_project_dir = "/home/ubuntu/openwebui"

enable_vagrant = False

enable_fluxcd = False

enable_backup_burp = False

backup_burp = {
    "ppa": "ppa:vshn/backup",
    "ppa_list_filename": "vshn-ubuntu-backup-noble.sources",
    "secret_store_app_name": "burp",
    "secret_store_local_pw_instance": "personal-laptop-instance",
    "secret_store_server_instance": "personal-server-laptop-server",
}

enable_displaylink_driver = False

gnome = {
    "enable_customize_gnome": False,
}

enable_ubuntu_cleanup = True

