import os

all = (
    ["@local"],
    {"_sudo_password": os.environ.get("SUDO_PASSWORD")},
)
