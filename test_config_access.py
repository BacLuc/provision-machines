#!/usr/bin/env python3
"""
Test script to verify that all configuration values are accessible
without defensive programming.
"""

import sys
from pathlib import Path

# Add the pyinfra directory to the path
sys.path.insert(0, str(Path(__file__).parent / "pyinfra"))

try:
    from pyinfra import host
    from pyinfra.facts import server
    
    # Test basic configuration access
    print("Testing configuration access...")
    
    # Core roles
    print(f"✓ basicsetup.enabled: {host.data.basicsetup.enabled}")
    print(f"✓ bash.enabled: {host.data.bash.enabled}")
    print(f"✓ python.enabled: {host.data.python.enabled}")
    print(f"✓ zsh.enabled: {host.data.zsh.enabled}")
    
    # Development tools
    print(f"✓ nvm enabled: {host.data.enable_nvm}")
    print(f"✓ kubectl.enabled: {host.data.kubectl.enabled}")
    print(f"✓ tmux.enabled: {host.data.tmux.enabled}")
    print(f"✓ enable_nvim: {host.data.enable_nvim}")
    print(f"✓ enable_lazygit: {host.data.enable_lazygit}")
    print(f"✓ enable_ollama: {host.data.enable_ollama}")
    print(f"✓ homebrew.enabled: {host.data.homebrew.enabled}")
    print(f"✓ snap.enabled: {host.data.snap.enabled}")
    print(f"✓ enable_sysctl: {host.data.enable_sysctl}")
    print(f"✓ motd.enable_disk_usage: {host.data.motd.enable_disk_usage}")
    print(f"✓ enable_alacritty: {host.data.enable_alacritty}")
    print(f"✓ enable_firefox: {host.data.enable_firefox}")
    print(f"✓ enable_zed: {host.data.enable_zed}")
    print(f"✓ enable_vifm: {host.data.enable_vifm}")
    print(f"✓ enable_jetbrains: {host.data.enable_jetbrains}")
    print(f"✓ okular.enabled: {host.data.okular.enabled}")
    
    # System integration
    print(f"✓ enable_ubuntu_desktop: {host.data.enable_ubuntu_desktop}")
    print(f"✓ hashicorp_apt_repo.enabled: {host.data.hashicorp_apt_repo.enabled}")
    print(f"✓ enable_hashicorp_vault_cli: {host.data.enable_hashicorp_vault_cli}")
    print(f"✓ enable_php_development: {host.data.enable_php_development}")
    print(f"✓ enable_openwebui: {host.data.enable_openwebui}")
    print(f"✓ enable_vagrant: {host.data.enable_vagrant}")
    print(f"✓ enable_fluxcd: {host.data.enable_fluxcd}")
    print(f"✓ enable_backup_burp: {host.data.enable_backup_burp}")
    print(f"✓ enable_displaylink_driver: {host.data.enable_displaylink_driver}")
    print(f"✓ gnome.enable_customize_gnome: {host.data.gnome.enable_customize_gnome}")
    print(f"✓ enable_ubuntu_cleanup: {host.data.enable_ubuntu_cleanup}")
    
    # Test nested configuration access
    print("\nTesting nested configuration access...")
    print(f"✓ basicsetup.additional_tools: {len(host.data.basicsetup.additional_tools)}")
    print(f"✓ kubectl.kubectl_neat_version: {host.data.kubectl.kubectl_neat_version}")
    print(f"✓ nvm.nvm_version: {host.data.nvm.nvm_version}")
    print(f"✓ php_development.php_version: {host.data.php_development.php_version}")
    print(f"✓ ubuntu_desktop.enable_shortcuts: {host.data.ubuntu_desktop.enable_shortcuts}")
    
    print("\n🎉 All configuration values accessible without defensive programming!")
    
except Exception as e:
    print(f"❌ Error accessing configuration: {e}")
    sys.exit(1)