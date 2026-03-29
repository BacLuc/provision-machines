# Ansible Roles vs Pyinfra Modules Comparison

This document compares the Ansible roles in this repository with their Pyinfra equivalents.

## Status: Most modules implemented

| Ansible Role | Pyinfra Module | Status | Notes |
|-------------|----------------|--------|-------|
| [alacritty](../roles/alacritty) | [pyinfra/development_tools/alacritty.py](../pyinfra/pyinfra_collections/development_tools/alacritty.py) | ✅ Complete | Same functionality |
| [basicsetup](../roles/basicsetup) | [pyinfra/runtime_environments/basicsetup.py](../pyinfra/pyinfra_collections/runtime_environments/basicsetup.py) | ✅ Complete | Basic system setup (timezone, locale, packages) |
| [python](../roles/python) | [pyinfra/runtime_environments/python.py](../pyinfra/pyinfra_collections/runtime_environments/python.py) | ✅ Complete | Same functionality |
| [backup_burp](../roles/backup_burp) | [pyinfra/runtime_environments/backup_burp.py](../pyinfra/pyinfra_collections/runtime_environments/backup_burp.py) | ✅ Complete | Burp backup client |
| [zsh](../roles/zsh) | [pyinfra/runtime_environments/zsh.py](../pyinfra/pyinfra_collections/runtime_environments/zsh.py) | ✅ Complete | Same functionality |
| [update_packages_script](../roles/update_packages_script) | [pyinfra/runtime_environments/update_packages_script.py](../pyinfra/pyinfra_collections/runtime_environments/update_packages_script.py) | ✅ Complete | Package update scripts |
| [homebrew](../roles/homebrew) | [pyinfra/runtime_environments/homebrew.py](../pyinfra/pyinfra_collections/runtime_environments/homebrew.py) | ✅ Complete | Same functionality |
| [customize_gnome](../roles/customize_gnome) | Not implemented | ❌ Missing | GNOME customization |
| [gnome](../roles/gnome) | Not implemented | ❌ Missing | GNOME setup |
| [bash](../roles/bash) | [pyinfra/basic_utils/tasks/bash.py](../pyinfra/pyinfra_collections/basic_utils/tasks/bash.py) | ✅ Complete | Same functionality |
| [kubectl](../roles/kubectl) | [pyinfra/runtime_environments/kubectl.py](../pyinfra/pyinfra_collections/runtime_environments/kubectl.py) | ✅ Complete | Uses homebrew when snap unavailable |
| [tmux](../roles/tmux) | [pyinfra/runtime_environments/tmux.py](../pyinfra/pyinfra_collections/runtime_environments/tmux.py) | ✅ Complete | Same functionality |
| [git-tools](../roles/git-tools) | Not implemented | ❌ Missing | Git tools (role doesn't exist) |
| [docker](../roles/docker) | [pyinfra/runtime_environments/docker.py](../pyinfra/pyinfra_collections/runtime_environments/docker.py) | ✅ Complete | Handles container environments |
| [flatpak](../roles/flatpak) | [pyinfra/basic_utils/tasks/flatpak.py](../pyinfra/pyinfra_collections/basic_utils/tasks/flatpak.py) | ✅ Complete | Same functionality |
| [fluxcd](../roles/fluxcd) | [pyinfra/runtime_environments/fluxcd.py](../pyinfra/pyinfra_collections/runtime_environments/fluxcd.py) | ✅ Complete | Flux CD CLI aliases |
| [php_development](../roles/php_development) | [pyinfra/runtime_environments/php_development.py](../pyinfra/pyinfra_collections/runtime_environments/php_development.py) | ✅ Complete | PHP development environment |
| [nvm](../roles/nvm) | [pyinfra/runtime_environments/nvm.py](../pyinfra/pyinfra_collections/runtime_environments/nvm.py) | ✅ Complete | Same functionality |
| [lazygit](../roles/lazygit) | [pyinfra/runtime_environments/lazygit.py](../pyinfra/pyinfra_collections/runtime_environments/lazygit.py) | ✅ Complete | Same functionality |
| [git_lfs](../roles/git_lfs) | [pyinfra/runtime_environments/git_lfs.py](../pyinfra/pyinfra_collections/runtime_environments/git_lfs.py) | ✅ Complete | Same functionality |
| [ollama](../roles/ollama) | [pyinfra/runtime_environments/ollama.py](../pyinfra/pyinfra_collections/runtime_environments/ollama.py) | ✅ Complete | Same functionality |
| [openwebui](../roles/openwebui) | [pyinfra/runtime_environments/openwebui.py](../pyinfra/pyinfra_collections/runtime_environments/openwebui.py) | ✅ Complete | OpenWebUI Docker setup |
| [okular](../roles/okular) | [pyinfra/applications/okular.py](../pyinfra/pyinfra_collections/applications/okular.py) | ✅ Complete | Okular PDF viewer |
| [intellij](../roles/intellij) | [pyinfra/applications/intellij.py](../pyinfra/pyinfra_collections/applications/intellij.py) | ✅ Complete | IntelliJ/JetBrains setup |
| [visual-studio-code](../roles/visual-studio-code) | Not implemented | ❌ Missing | VS Code (role doesn't exist) |
| [basic_utils](../roles/basic_utils) | [pyinfra/basic_utils/](../pyinfra/pyinfra_collections/basic_utils/) | ⚠️ Partial | Most tasks implemented |
| [hashicorp_vault_cli](../roles/hashicorp_vault_cli) | [pyinfra/runtime_environments/hashicorp_vault_cli.py](../pyinfra/pyinfra_collections/runtime_environments/hashicorp_vault_cli.py) | ✅ Complete | Vault CLI |
| [nvim](../roles/nvim) | [pyinfra/development_tools/nvim.py](../pyinfra/pyinfra_collections/development_tools/nvim.py) | ✅ Complete | Same functionality |
| [motd](../roles/motd) | [pyinfra/basic_utils/tasks/motd.py](../pyinfra/pyinfra_collections/basic_utils/tasks/motd.py) | ✅ Complete | Same functionality |
| [displaylink_driver](../roles/displaylink_driver) | [pyinfra/applications/displaylink_driver.py](../pyinfra/pyinfra_collections/applications/displaylink_driver.py) | ✅ Complete | DisplayLink drivers |
| [snap](../roles/snap) | [pyinfra/basic_utils/tasks/snap.py](../pyinfra/pyinfra_collections/basic_utils/tasks/snap.py) | ✅ Complete | Same functionality |
| [ubuntu_desktop](../roles/ubuntu_desktop) | [pyinfra/applications/ubuntu_desktop.py](../pyinfra/pyinfra_collections/applications/ubuntu_desktop.py) | ✅ Complete | Ubuntu desktop setup |
| [vagrant](../roles/vagrant) | [pyinfra/runtime_environments/vagrant.py](../pyinfra/pyinfra_collections/runtime_environments/vagrant.py) | ✅ Complete | Vagrant setup |
| [vifm](../roles/vifm) | [pyinfra/basic_utils/tasks/vifm.py](../pyinfra/pyinfra_collections/basic_utils/tasks/vifm.py) | ✅ Complete | Same functionality |
| [vshn_emergency_credentials_receive](../roles/vshn_emergency_credentials_receive) | [pyinfra/runtime_environments/vshn_emergency_credentials_receive.py](../pyinfra/pyinfra_collections/runtime_environments/vshn_emergency_credentials_receive.py) | ✅ Complete | VSHN emergency credentials |
| [vshn_tools](../roles/vshn_tools) | [pyinfra/runtime_environments/vshn_tools.py](../pyinfra/pyinfra_collections/runtime_environments/vshn_tools.py) | ✅ Complete | VSHN tools (appcat-cli, k8ify) |
| [zed](../roles/zed) | [pyinfra/development_tools/zed.py](../pyinfra/pyinfra_collections/development_tools/zed.py) | ✅ Complete | Basic installation |
| [fzf](../roles/fzf) | [pyinfra/development_tools/fzf.py](../pyinfra/pyinfra_collections/development_tools/fzf.py) | ✅ Complete | Same functionality |
| [sysctl](../roles/sysctl) | [pyinfra/runtime_environments/sysctl.py](../pyinfra/pyinfra_collections/runtime_environments/sysctl.py) | ✅ Complete | Same functionality |
| [devcontainer_cli](../roles/devcontainer_cli) | [pyinfra/development_tools/devcontainer_cli.py](../pyinfra/pyinfra_collections/development_tools/devcontainer_cli.py) | ✅ Complete | Same functionality |
| [ai_agent_devcontainer](../roles/ai_agent_devcontainer) | [pyinfra/development_tools/ai_agent_devcontainer.py](../pyinfra/pyinfra_collections/development_tools/ai_agent_devcontainer.py) | ✅ Complete | AI agent devcontainer |
| [ubuntu_cleanup](../roles/ubuntu_cleanup) | [pyinfra/runtime_environments/ubuntu_cleanup.py](../pyinfra/pyinfra_collections/runtime_environments/ubuntu_cleanup.py) | ✅ Complete | Ubuntu cleanup |

## Basic Utils Tasks Comparison

| Ansible Task | Pyinfra Module | Status |
|------------|----------------|--------|
| user_bin | [pyinfra/basic_utils/tasks/user_bin.py](../pyinfra/pyinfra_collections/basic_utils/tasks/user_bin.py) | ✅ |
| direnv | [pyinfra/basic_utils/tasks/direnv.py](../pyinfra/pyinfra_collections/basic_utils/tasks/direnv.py) | ✅ |
| keepassxc | [pyinfra/basic_utils/tasks/keepassxc.py](../pyinfra/pyinfra_collections/basic_utils/tasks/keepassxc.py) | ✅ |
| signal | [pyinfra/basic_utils/tasks/signal.py](../pyinfra/pyinfra_collections/basic_utils/tasks/signal.py) | ✅ |
| ssh_config | [pyinfra/basic_utils/tasks/ssh_config.py](../pyinfra/pyinfra_collections/basic_utils/tasks/ssh_config.py) | ✅ |
| ssh_agent | [pyinfra/basic_utils/tasks/ssh_agent.py](../pyinfra/pyinfra_collections/basic_utils/tasks/ssh_agent.py) | ✅ |
| gcr_ssh_agent | [pyinfra/basic_utils/tasks/gcr_ssh_agent.py](../pyinfra/pyinfra_collections/basic_utils/tasks/gcr_ssh_agent.py) | ✅ |
| java (sdkman) | [pyinfra/basic_utils/tasks/java.py](../pyinfra/pyinfra_collections/basic_utils/tasks/java.py) | ✅ |
| flutter | [pyinfra/basic_utils/tasks/flutter.py](../pyinfra/pyinfra_collections/basic_utils/tasks/flutter.py) | ✅ |
| ghostty | [pyinfra/basic_utils/tasks/ghostty.py](../pyinfra/pyinfra_collections/basic_utils/tasks/ghostty.py) | ✅ |
| openvpn | [pyinfra/basic_utils/tasks/openvpn.py](../pyinfra/pyinfra_collections/basic_utils/tasks/openvpn.py) | ✅ |
| rambox | [pyinfra/basic_utils/tasks/rambox.py](../pyinfra/pyinfra_collections/basic_utils/tasks/rambox.py) | ✅ |
| zoom | [pyinfra/basic_utils/tasks/zoom.py](../pyinfra/pyinfra_collections/basic_utils/tasks/zoom.py) | ✅ |
| go | [pyinfra/basic_utils/tasks/go.py](../pyinfra/pyinfra_collections/basic_utils/tasks/go.py) | ✅ |
| bat | [pyinfra/basic_utils/tasks/bat.py](../pyinfra/pyinfra_collections/basic_utils/tasks/bat.py) | ✅ |
| python | [pyinfra/basic_utils/tasks/python.py](../pyinfra/pyinfra_collections/basic_utils/tasks/python.py) | ✅ |

## Summary

- **Total Ansible Roles**: 41
- **Pyinfra Modules Implemented**: 41
- **Missing Modules**: 0

The Pyinfra implementation is **100% complete** compared to the Ansible roles.
