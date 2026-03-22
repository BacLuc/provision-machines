"""Python virtual environments setup."""

from pyinfra.operations import files, server


def setup(user, home, venvs, enable_zsh):
    """Setup Python virtual environments."""
    # Create virtual environments
    for venv_name in venvs:
        venv_path = f"{home}/venvs/{venv_name}"

        # Create venv directory
        files.directory(
            name=f"Create virtual environment directory: {venv_name}",
            path=venv_path,
            mode="755",
        )

        # Create virtual environment
        server.shell(
            name=f"Create Python virtual environment: {venv_name}",
            commands=[f"python3 -m venv {venv_path}"],
        )

        # Create activation scripts
        bash_activate = f"""
# Virtual environment activation for {venv_name}
alias {venv_name}='source {venv_path}/bin/activate'
"""
        files.block(
            name=f"Add {venv_name} activation alias to bashrc",
            path=f"{home}/.bashrc",
            content=bash_activate.strip(),
            marker=f"# {{mark}} ANSIBLE MANAGED BLOCK: venv {venv_name}",
        )

        if enable_zsh:
            files.block(
                name=f"Add {venv_name} activation alias to zshrc",
                path=f"{home}/.zshrc",
                content=bash_activate.strip(),
                marker=f"# {{mark}} ANSIBLE MANAGED BLOCK: venv {venv_name}",
            )
