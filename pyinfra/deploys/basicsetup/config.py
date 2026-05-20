# Default configuration for basicsetup role
# These values can be overridden in group data

# Package lists matching ci-inventory.yaml
basic_tools = [
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
]

additional_tools = [
    "ansible-lint",
    "apt-transport-https",
    "bat",
    "clang",
    "cmake",
    "build-essential",
    "cloc",
    "curl",
    "git",
    "graphviz",
    "jq",
    "libglu1-mesa",
    "libgtk-3-dev",
    "libstdc++-12-dev",
    "ninja-build",
    "net-tools",
    "ocrmypdf",
    "pkg-config",
    "procps",
    "tig",
    "yamllint",
    "xz-utils",
]

# Default timezone and locale
timezone = "Europe/Zurich"
locale = "en_US.UTF-8"
