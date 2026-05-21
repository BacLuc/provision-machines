from pyinfra import host
from pyinfra.operations import apt, files

def deploy_alacritty():
    enable_alacritty = host.data.get('enable_alacritty', False) 
    
    if not enable_alacritty:
        return

    # Install Alacritty
    apt.packages(
        name="Install alacritty",
        packages=["alacritty"],
        present=True,
        _sudo=True,
    )

    # Create config directory
    files.directory(
        name="Create Alacritty config directory",
        path="~/.config/alacritty",
        present=True,
        mode="0755",
    )

    # Download theme
    # renovate: datasource=github-tags depName=catppuccin/alacritty
    theme_commit = "f6cb5a5c2b404cdaceaff193b9c52317f62c62f7"
    files.download(
        name="Download Catppuccin Mocha theme",
        src=f"https://raw.githubusercontent.com/catppuccin/alacritty/{theme_commit}/catppuccin-mocha.toml",
        dest="~/.config/alacritty/catppuccin-mocha.toml",
        mode="0644",
    )

    # Deploy config template
    # Instead of host.data, use dictionary directly since we might be mocking the data
    # or get it from standard ways. For now let's set defaults if it doesn't exist
    alacritty_config = host.data.get('alacritty', {})
    font_size = alacritty_config.get('font_size', 12)
    
    files.template(
        name="Provision Alacritty config",
        src="deploys/development_tools/alacritty/alacritty.toml.j2",
        dest="~/.config/alacritty/alacritty.toml",
        mode="0644",
        font_size=font_size,
    )

deploy_alacritty()

