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
    "enabled": True,
}

homebrew = {
    "enabled": True,
}

snap = {
    "enabled": True,
}

snaps: list[str] = [
    "firefox",
]

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

hashicorp_apt_repo = {
    "enabled": True,
}

hashicorp_vault_cli = {
    "enabled": True,
}

openwebui = {
    "enabled": True,
}

vagrant = {
    "enabled": True,
}

ubuntu_cleanup = {
    "enabled": True,
}
