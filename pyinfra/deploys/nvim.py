from pyinfra import host
from pyinfra.operations import files, server

user = host.data.get("user", "ubuntu")

if host.data.enable_nvim:
    
    # Install neovim using homebrew (would need to be implemented)
    server.shell(
        name="Install neovim",
        commands=[f"{host.data.get('homebrew_binaries_path', f'/home/{user}/bin')}/brew install neovim"],
    )
    
    # Install NormalNeovim distribution
    server.shell(
        name="Install NormalNeovim distribution",
        commands=[
            "rm -rf ~/.config/nvim",
            "git clone https://github.com/BacLuc/NormalNvim.git ~/.config/nvim",
        ],
    )
    
    files.put(
        name="Add script to update nvim",
        dest=f"{host.data.get('update_packages_script', {}).get('dir', '/usr/local/bin')}/normal-neovim-upgrade",
        content=f"""#!/bin/sh
user="{user}"
version=origin/main

su "$user" -c "git -C /home/{user}/.config/nvim fetch"
su "$user" -c "git -C /home/{user}/.config/nvim reset --hard $version"
""",
        mode="755",
        _sudo=True,
    )
    
    # Check current vim alternatives
    server.shell(
        name="Check current vim alternatives",
        commands=["update-alternatives --query vim"],
    )
    
    # Add vim to update-alternatives if it doesn't exist
    server.shell(
        name="Add vim to update-alternatives",
        commands=[f"update-alternatives --install /usr/bin/vim vim {host.data.get('homebrew_binaries_path', f'/home/{user}/bin')}/nvim 1"],
    )
    
    # Set nvim as the default vim alternative
    server.shell(
        name="Set nvim as the default vim alternative",
        commands=[f"update-alternatives --set vim {host.data.get('homebrew_binaries_path', f'/home/{user}/bin')}/nvim"],
    )
    
    # Check current vi alternatives
    server.shell(
        name="Check current vi alternatives",
        commands=["update-alternatives --query vi"],
    )
    
    # Add vi to update-alternatives if it doesn't exist
    server.shell(
        name="Add vi to update-alternatives",
        commands=[f"update-alternatives --install /usr/bin/vi vi {host.data.get('homebrew_binaries_path', f'/home/{user}/bin')}/nvim 1"],
    )
    
    # Set nvim as the default vi alternative
    server.shell(
        name="Set nvim as the default vi alternative",
        commands=[f"update-alternatives --set vi {host.data.get('homebrew_binaries_path', f'/home/{user}/bin')}/nvim"],
    )