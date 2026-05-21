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

