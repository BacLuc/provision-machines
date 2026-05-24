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
    if host.data.get("basicsetup", {}).get("enabled", False):
        basicsetup()
    
    if host.data.get("bash", {}).get("enabled", False):
        bash()
    
    if host.data.get("python", {}).get("enabled", False):
        python()
    
    if host.data.get("zsh", {}).get("enabled", False):
        zsh()
    
    if host.data.get("basic_utils", {}).get("enabled", False):
        basic_utils_deploy()
    
    if host.data.get("cleanup_scripts", {}).get("enabled", False):
        cleanup_scripts_deploy()
    
    if host.data.get("docker", {}).get("enabled", False):
        docker_deploy()
    
    if host.data.get("flatpak", {}).get("enabled", False):
        flatpak_deploy()
    
    if host.data.get("fzf", {}).get("enabled", False):
        fzf_deploy()
    
    if host.data.get("git_lfs", {}).get("enabled", False):
        git_lfs_deploy()
    
    if (host.data.get("basic_utils", {}).get("enable_nvm", False) or 
        host.data.get("enable_nvm", False)):
        nvm()
    
    if host.data.get("kubectl", {}).get("enabled", False):
        kubectl()
    
    if host.data.get("tmux", {}).get("enabled", False):
        tmux()
    
    if host.data.get("enable_nvim", False):
        nvim()
    
    if host.data.get("enable_lazygit", False):
        lazygit()
    
    if host.data.get("enable_ollama", False):
        ollama()
    
    if host.data.get("homebrew", {}).get("enabled", False):
        homebrew()
    
    if host.data.get("snap", {}).get("enabled", False):
        snap()
    
    if host.data.get("enable_sysctl", False):
        sysctl()
    
    if host.data.get("motd", {}).get("enable_disk_usage", False):
        motd()
    
    if host.data.get("enable_alacritty", False):
        alacritty()
    
    if host.data.get("enable_firefox", False):
        firefox()
    
    if host.data.get("enable_zed", False):
        zed()
    
    if host.data.get("enable_vifm", False):
        vifm()
    
    if host.data.get("enable_jetbrains", False):
        intellij()
    
    if host.data.get("okular", {}).get("enabled", False):
        okular()
    
    if host.data.get("enable_ubuntu_desktop", True):
        ubuntu_desktop()
    
    if host.data.get("hashicorp_apt_repo", {}).get("enabled", False):
        hashicorp_apt_repo()
    
    if host.data.get("enable_hashicorp_vault_cli", False):
        hashicorp_vault_cli()
    
    if host.data.get("enable_php_development", False):
        php_development()
    
    if host.data.get("enable_openwebui", False):
        openwebui()
    
    if host.data.get("enable_vagrant", False):
        vagrant()
    
    if host.data.get("enable_fluxcd", False):
        fluxcd()
    
    if host.data.get("enable_backup_burp", False):
        backup_burp()
    
    if host.data.get("enable_displaylink_driver", False):
        displaylink_driver()
    
    if host.data.get("gnome", {}).get("enable_customize_gnome", False):
        gnome()
    
    if host.data.get("enable_ubuntu_cleanup", True):
        ubuntu_cleanup()