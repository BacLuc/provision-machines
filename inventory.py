import os

# noinspection PyShadowingBuiltins
all = (
    ["@local"],
    {"_sudo_password": os.environ.get("SUDO_PASSWORD")},
)
