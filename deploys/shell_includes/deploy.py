import io

from pyinfra import host
from pyinfra.operations import files

from operations.user import get_user_name

user = get_user_name()
loader_dir = f"/home/{user}/.config/shell"

if host.data.shell_includes["enabled"]:
    includes = [
        (".bashrc.d", ".bashrc", "sh"),
        (".bash_aliases.d", ".bash_aliases", "sh"),
    ]
    if host.data.zsh["enabled"]:
        includes.append((".zshrc.d", ".zshrc", "zsh"))

    for include_dir, rc_file, shell in includes:
        files.directory(
            name=f"Create {include_dir}",
            path=f"/home/{user}/{include_dir}",
            user=user,
            group=user,
            mode="755",
        )

        if shell == "zsh":
            loader = f"""\
    for rc in /home/{user}/{include_dir}/*(.N); do
      source "$rc"
    done
    """
        else:
            loader = f"""\
    for rc in /home/{user}/{include_dir}/*; do
      [ -f "$rc" ] && . "$rc"
    done
    """

        loader_path = f"{loader_dir}/load-{include_dir}.{shell}"
        files.put(
            name=f"Add {include_dir} loader",
            src=io.StringIO(loader),
            dest=loader_path,
            user=user,
            group=user,
            mode="644",
        )

        files.block(
            name=f"Source {include_dir} in {rc_file}",
            path=f"/home/{user}/{rc_file}",
            marker="# {mark} PYINFRA MANAGED BLOCK: source " + include_dir,
            content=f"source {loader_path}",
        )
