from .backup_burp import configure_backup_burp
from .basicsetup import configure_basicsetup
from .docker import configure_docker
from .fluxcd import configure_fluxcd
from .git_lfs import configure_git_lfs
from .hashicorp_vault_cli import configure_hashicorp_vault_cli
from .homebrew import configure_homebrew
from .kubectl import configure_kubectl
from .lazygit import configure_lazygit
from .nvm import configure_nvm
from .ollama import configure_ollama
from .openwebui import configure_openwebui
from .php_development import configure_php_development
from .python import configure_python
from .sysctl import configure_sysctl
from .tmux import configure_tmux
from .ubuntu_cleanup import configure_ubuntu_cleanup
from .update_packages_script import configure_update_packages_script
from .vagrant import configure_vagrant
from .vshn_emergency_credentials_receive import configure_vshn_emergency_credentials_receive
from .vshn_tools import configure_vshn_tools
from .zsh import configure_zsh

__all__ = [
    "configure_backup_burp",
    "configure_basicsetup",
    "configure_docker",
    "configure_fluxcd",
    "configure_git_lfs",
    "configure_hashicorp_vault_cli",
    "configure_homebrew",
    "configure_kubectl",
    "configure_lazygit",
    "configure_nvm",
    "configure_ollama",
    "configure_openwebui",
    "configure_php_development",
    "configure_python",
    "configure_sysctl",
    "configure_tmux",
    "configure_ubuntu_cleanup",
    "configure_update_packages_script",
    "configure_vagrant",
    "configure_vshn_emergency_credentials_receive",
    "configure_vshn_tools",
    "configure_zsh",
]
