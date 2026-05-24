from pyinfra import host
from pyinfra.operations import local

from .deploys import basicsetup, bash, python, zsh, nvm, kubectl, tmux, nvim, lazygit, ollama, homebrew, snap, sysctl, motd, alacritty, firefox, zed, vifm, intellij, okular, ubuntu_desktop, hashicorp_apt_repo, hashicorp_vault_cli, php_development, openwebui, vagrant, fluxcd, backup_burp, displaylink_driver, gnome, ubuntu_cleanup
from .deploys.basic_utils import deploy as basic_utils_deploy
from .deploys.cleanup_scripts import deploy as cleanup_scripts_deploy
from .deploys.docker import deploy as docker_deploy
from .deploys.flatpak import deploy as flatpak_deploy
from .deploys.fzf import deploy as fzf_deploy
from .deploys.git_lfs import deploy as git_lfs_deploy


def deploy():
    # Core infrastructure
    if host.data.basicsetup.enabled:
        basicsetup()
    
    if host.data.bash.enabled:
        bash()
    
    if host.data.python.enabled:
        python()
    
    if host.data.zsh.enabled:
        zsh()
    
    if host.data.basic_utils.enabled:
        basic_utils_deploy()
    
    if host.data.cleanup_scripts.enabled:
        cleanup_scripts_deploy()
    
    if host.data.docker.enabled:
        docker_deploy()
    
    if host.data.flatpak.enabled:
        flatpak_deploy()
    
    if host.data.fzf.enabled:
        fzf_deploy()
    
    if host.data.git_lfs.enabled:
        git_lfs_deploy()
    
    # Development tools
    if host.data.basic_utils.enable_nvm or host.data.enable_nvm:
        nvm()
    
    if host.data.kubectl.enabled:
        kubectl()
    
    if host.data.tmux.enabled:
        tmux()
    
    if host.data.enable_nvim:
        nvim()
    
    if host.data.enable_lazygit:
        lazygit()
    
    if host.data.enable_ollama:
        ollama()
    
    if host.data.homebrew.enabled:
        homebrew()
    
    if host.data.snap.enabled:
        snap()
    
    if host.data.enable_sysctl:
        sysctl()
    
    if host.data.motd.enable_disk_usage:
        motd()
    
    if host.data.enable_alacritty:
        alacritty()
    
    if host.data.enable_firefox:
        firefox()
    
    if host.data.enable_zed:
        zed()
    
    if host.data.enable_vifm:
        vifm()
    
    if host.data.enable_jetbrains:
        intellij()
    
    if host.data.okular.enabled:
        okular()
    
    # System integration (mostly enabled by default)
    if host.data.enable_ubuntu_desktop:
        ubuntu_desktop()
    
    if host.data.hashicorp_apt_repo.enabled:
        hashicorp_apt_repo()
    
    if host.data.enable_hashicorp_vault_cli:
        hashicorp_vault_cli()
    
    if host.data.enable_php_development:
        php_development()
    
    if host.data.enable_openwebui:
        openwebui()
    
    if host.data.enable_vagrant:
        vagrant()
    
    if host.data.enable_fluxcd:
        fluxcd()
    
    if host.data.enable_backup_burp:
        backup_burp()
    
    if host.data.enable_displaylink_driver:
        displaylink_driver()
    
    if host.data.gnome.enable_customize_gnome:
        gnome()
    
    # Always run cleanup
    if host.data.enable_ubuntu_cleanup:
        ubuntu_cleanup()