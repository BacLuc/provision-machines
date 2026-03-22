#!/usr/bin/env python3
"""
Main Pyinfra deployment script.

Usage:
    pyinfra @local deploy.py
    pyinfra @local deploy.py --data "enable_zsh=true"
"""

from pyinfra_collections.development_tools import (
    configure_alacritty,
    configure_fzf,
    configure_nvim,
)
from pyinfra_collections.runtime_environments import (
    configure_docker,
    configure_nvm,
    configure_python,
    configure_tmux,
    configure_zsh,
)

# Call all configure functions - each checks its own enable flag
configure_docker(_sudo=True)
configure_nvm(_sudo=True)
configure_python(_sudo=True)
configure_tmux(_sudo=True)
configure_zsh(_sudo=True)
configure_alacritty(_sudo=True)
configure_nvim(_sudo=True)
configure_fzf(_sudo=True)
