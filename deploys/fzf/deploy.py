from pyinfra import host, local
from pyinfra.facts.files import File
from pyinfra.operations import server

from operations.homebrew import HOMEBREW_BIN, user_brew_bin
from operations.user import get_user_name

user = get_user_name()

if host.data.fzf["enabled"]:
    local.include("deploys/homebrew/deploy.py")
    if host.get_fact(File, f"{HOMEBREW_BIN}/fzf") is None:
        server.shell(
            name="Install fzf via brew",
            commands=[user_brew_bin(user) + " install fzf"],
        )
