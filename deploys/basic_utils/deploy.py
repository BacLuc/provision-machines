from pyinfra.facts.files import Directory, File

from operations.filesystem import DEPLOYS_DIR, dirname_of
from operations.user import get_user_name
from pyinfra import host, local
from pyinfra.operations import (
    apt,
    files,
    flatpak,
    server,
    snap,
)

user = get_user_name()

basic_utils = host.data.basic_utils
if "socket" not in basic_utils["gcr_ssh_agent"]:
    # hardcoded for now
    basic_utils["gcr_ssh_agent"]["socket"] = "/run/user/1000/gcr/ssh"

files.directory(
    name="Setup user bin dir",
    path=f"/home/{user}/bin",
    user=user,
    group=user,
    mode="755",
)

files.block(
    name="Source user bin and ~/.local/bin dir in bash",
    path=f"/home/{user}/.bashrc",
    marker="# {mark} ANSIBLE MANAGED BLOCK: bin of user",
    content=f'export PATH="/home/{user}/bin:/home/{user}/.local/bin:$PATH"',
    try_prevent_shell_expansion=True,
)

zsh_enabled = host.data.zsh["enabled"]
if zsh_enabled:
    files.block(
        name="Source user bin and ~/.local/bin dir in zsh",
        path=f"/home/{user}/.zshrc",
        marker="# {mark} ANSIBLE MANAGED BLOCK: bin of user",
        content=f'export PATH="/home/{user}/bin:/home/{user}/.local/bin:$PATH"',
        try_prevent_shell_expansion=True,
    )

if basic_utils["enable_direnv"]:
    apt.packages(
        name="Install direnv package",
        packages=["direnv"],
        _sudo=True,
    )

    files.block(
        name="Source direnv bash",
        path=f"/home/{user}/.bashrc",
        marker="# {mark} ANSIBLE MANAGED BLOCK: source direnv",
        content='eval "$(direnv hook bash)"',
        try_prevent_shell_expansion=True,
    )

    if zsh_enabled:
        files.block(
            name="Source direnv zsh",
            path=f"/home/{user}/.zshrc",
            marker="# {mark} ANSIBLE MANAGED BLOCK: source direnv",
            content='eval "$(direnv hook zsh)"',
            try_prevent_shell_expansion=True,
        )

gcr_ssh_agent = basic_utils["gcr_ssh_agent"]
gcr_ssh_agent_socket = gcr_ssh_agent["socket"]
if basic_utils["enable_keepassxc"]:
    local.include(f"{DEPLOYS_DIR}/flatpak/deploy.py")
    flatpak.packages(packages=["org.keepassxc.KeePassXC"])

    files.line(
        name="modify desktop file",
        path=f"/home/{user}/.bash_aliases",
        line="^Exec=",
        replace="Exec=/usr/bin/flatpak run --branch=stable --arch=x86_64 --command=keepassxc --file-forwarding org.keepassxc.KeePassXC --platform xcb @@ %f @@",
        present=True,
    )

    if gcr_ssh_agent["enable"]:
        override_exists = server.shell(
            name="Check if override already exists",
            commands="flatpak override org.keepassxc.KeePassXC --show",
        )

        override = f"filesystems={gcr_ssh_agent_socket};"
        server.shell(
            name="Configure override",
            commands=f"flatpak override org.keepassxc.KeePassXC --{override}",
            _if=lambda: gcr_ssh_agent_socket not in override_exists.stdout,
        )

        files.block(
            name="Configure ssh-agent sock",
            path=f"/home/{user}/.var/app/org.keepassxc.KeePassXC/cache/keepassxc/keepassxc.ini",
            marker="# {mark} ANSIBLE MANAGED BLOCK: configure ssh-agent",
            content=f"AuthSockOverride={gcr_ssh_agent_socket}",
        )

    keepass_config = f"/home/{user}/.var/app/org.keepassxc.KeePassXC/config/keepassxc/keepassxc.ini"
    keepass_cache_ini = f"/home/{user}/.var/app/org.keepassxc.KeePassXC/cache/keepassxc/keepassxc.ini"

    files.directory(
        name="Ensure KeePassXC cache directory exists",
        path=f"/home/{user}/.var/app/org.keepassxc.KeePassXC/config/keepassxc",
        user=user,
        mode="775",
    )

    files.block(
        name="Configure auto type in KeePassXC",
        path=keepass_config,
        marker="# {mark} PYINFRA MANAGED BLOCK: configure auto type",
        content="""GlobalAutoTypeKey=65
    GlobalAutoTypeModifiers=201326592""",
    )

    files.directory(
        name="Ensure KeePassXC cache directory exists",
        path=f"/home/{user}/.var/app/org.keepassxc.KeePassXC/cache/keepassxc",
        user=user,
        mode="775",
    )

    if gcr_ssh_agent["enable"]:
        files.line(
            name="Add SSHAgent section to keepassxc.ini",
            path=keepass_cache_ini,
            line="^\\[SSHAgent\\]",
            replace="[SSHAgent]",
            present=True,
        )

        files.block(
            name="Add SSHAgent section to keepassxc.ini",
            path=keepass_cache_ini,
            marker="# {mark} ANSIBLE MANAGED BLOCK: configure ssh-agent",
            line="^\\[SSHAgent\\]",
            after=True,
            content=f"AuthSockOverride={gcr_ssh_agent_socket}",
        )

if basic_utils["enable_signal"]:
    snap.package(packages=["signal-desktop"], _sudo=True)

if basic_utils["enable_ssh_config_dir"]:
    files.directory(
        name="Setup ssh config dir",
        path=f"/home/{user}/.ssh/config.d",
        user=user,
        group=user,
        mode="700",
    )

    files.template(
        name="Add ssh-config",
        src=f"{dirname_of(__file__)}/templates/ssh-config.j2",
        dest=f"/home/{user}/.ssh/config",
        user=user,
        group=user,
        mode="600",
        basic_utils=basic_utils,
    )

# if basic_utils["ssh_key"]["enable"] and basic_utils["ssh_agent"]["enable"]:
#     files.block(
#         name="Setup ssh-agent for bash",
#         path=f"/home/{user}/.bashrc",
#         marker="# {mark} ANSIBLE MANAGED BLOCK: start ssh agent",
#         content=f"""if [ -z "$(pgrep ssh-agent)" ]; then
#   rm -rf /tmp/ssh-*
#   eval $(ssh-agent -s) > /dev/null
# fi
# export SSH_AGENT_PID=$(pgrep ssh-agent)
# export SSH_AUTH_SOCK=$(find /tmp/ssh-* -name 'agent.*')
#
# if [[ ! $(ssh-add -l | grep "{basic_utils["ssh_key"]["comment"]}") ]]; then
#   ssh_key_path="$HOME/.ssh/{basic_utils["ssh_key"]["filename"]}"
#   if [[ -f "$ssh_key_path" ]]; then
#     ssh-add "$ssh_key_path"
#   fi
# fi""",
#         try_prevent_shell_expansion=True,
#     )
#
#     if zsh_enabled:
#         files.block(
#             name="Setup ssh-agent for zsh",
#             path=f"/home/{user}/.zshrc",
#             marker="# {mark} ANSIBLE MANAGED BLOCK: start ssh agent",
#             content=f"""if [ -z "$(pgrep ssh-agent)" ]; then
#   rm -rf /tmp/ssh-*
#   eval $(ssh-agent -s) > /dev/null
# fi
# export SSH_AGENT_PID=$(pgrep ssh-agent)
# export SSH_AUTH_SOCK=$(find /tmp/ssh-* -name 'agent.*')
#
# if [[ ! $(ssh-add -l | grep "{basic_utils["ssh_key"]["comment"]}") ]]; then
#   ssh_key_path="$HOME/.ssh/{basic_utils["ssh_key"]["filename"]}"
#   if [[ -f "$ssh_key_path" ]]; then
#     ssh-add "$ssh_key_path"
#   fi
# fi""",
#             try_prevent_shell_expansion=True,
#         )

if gcr_ssh_agent["enable"]:
    ssh_key_path = f"/home/{user}/.ssh/{basic_utils['ssh_key']['filename']}"
    ssh_key_exists = host.get_fact(File, ssh_key_path)

    # not tested yet
    if not ssh_key_exists:
        import secrets
        import string

        alphabet = string.ascii_letters + string.digits
        password = "".join(secrets.choice(alphabet) for i in range(32))

        server.shell(
            name="Create ssh-key",
            commands=[f'ssh-keygen -f {ssh_key_path} -C "{basic_utils["ssh_key"]["comment"]}" -N "{password}"'],
        )

        server.shell(
            name="Add ssh-key to ssh-agent on login via secret-tool",
            commands=[
                f'secret-tool store --label="Unlock ssh key {basic_utils["ssh_key"]["filename"]}" unique ssh-store:/home/{user}/.ssh/{basic_utils["ssh_key"]["filename"]}'
            ],
            _stdin=password,
        )

    files.block(
        name="Setup gcr-ssh-agent for bash",
        path=f"/home/{user}/.bashrc",
        marker="# {mark} ANSIBLE MANAGED BLOCK: start gcr ssh agent",
        content=f"""export SSH_AUTH_SOCK={gcr_ssh_agent_socket}

if [[ ! $(ssh-add -l | grep "{basic_utils["ssh_key"]["comment"]}") ]]; then
  ssh_key_path="$HOME/.ssh/{basic_utils["ssh_key"]["filename"]}"
  if [[ -f "$ssh_key_path" ]]; then
    ssh-add "$ssh_key_path"
  fi
fi""",
        try_prevent_shell_expansion=True,
    )

    if zsh_enabled:
        files.block(
            name="Setup gcr-ssh-agent for zsh",
            path=f"/home/{user}/.zshrc",
            marker="# {mark} ANSIBLE MANAGED BLOCK: start gcr ssh agent",
            content=f"""export SSH_AUTH_SOCK={gcr_ssh_agent_socket}

if [[ ! $(ssh-add -l | grep "{basic_utils["ssh_key"]["comment"]}") ]]; then
  ssh_key_path="$HOME/.ssh/{basic_utils["ssh_key"]["filename"]}"
  if [[ -f "$ssh_key_path" ]]; then
    ssh-add "$ssh_key_path"
  fi
fi""",
            try_prevent_shell_expansion=True,
        )

if basic_utils["enable_java"]:
    """TODO: install skdman
    - name: check if sdkman is installed
  when: basic_utils.enable_java | default(false)
  ansible.builtin.stat:
    path: ~/.sdkman
  register: basic_utils__sdkman

- name: install sdkman # noqa command-instead-of-module
  when: (basic_utils.enable_java | default(false)) and (basic_utils__sdkman.stat.exists is false)
  ansible.builtin.shell: |
    curl -s https://get.sdkman.io | bash
    """

    files.block(
        name="Add sdkman to .bashrc",
        path=f"/home/{user}/.bashrc",
        marker="# {mark} ANSIBLE MANAGED BLOCK: sdkman-init",
        content="""export SDKMAN_DIR="$HOME/.sdkman"
[[ -s "$HOME/.sdkman/bin/sdkman-init.sh" ]] && source "$HOME/.sdkman/bin/sdkman-init.sh\"""",
        try_prevent_shell_expansion=True,
    )

    if zsh_enabled:
        files.block(
            name="Add sdkman to .zshrc",
            path=f"/home/{user}/.zshrc",
            marker="# {mark} ANSIBLE MANAGED BLOCK: sdkman-init",
            content="""export SDKMAN_DIR="$HOME/.sdkman"
[[ -s "$HOME/.sdkman/bin/sdkman-init.sh" ]] && source "$HOME/.sdkman/bin/sdkman-init.sh\"""",
            try_prevent_shell_expansion=True,
        )

if basic_utils["enable_flutter"]:
    fvm_flutter_dir = host.get_fact(Directory, f"/home/{user}/.fvm_flutter")

    fvm_version = "3.2.1"

    server.shell(
        name="Install fvm",
        commands=f"""
curl -fsSL https://raw.githubusercontent.com/leoafarias/fvm/refs/tags/{fvm_version}/scripts/install.sh |  bash -s -- {fvm_version}
rm -rf /usr/local/bin/fvm
mv /root/.fvm_flutter /home/{user}/.fvm_flutter
chown -R {user}:{user} /home/{user}/.fvm_flutter
""",
        _if=lambda: fvm_flutter_dir is None,
    )

    files.block(
        name="Add fvm to path for bash",
        path=f"/home/{user}/.bashrc",
        marker="# {mark} ANSIBLE MANAGED BLOCK: add fvm to PATH",
        content=f'export PATH="/home/{user}/.fvm_flutter/bin:$PATH"',
        try_prevent_shell_expansion=True,
    )

    if zsh_enabled:
        files.block(
            name="Add fvm to path for zsh",
            path=f"/home/{user}/.zshrc",
            marker="# {mark} ANSIBLE MANAGED BLOCK: add fvm to PATH",
            content=f'export PATH="/home/{user}/.fvm_flutter/bin:$PATH"',
            try_prevent_shell_expansion=True,
        )

    """
    TODO
    - name: install android studio
      become: true
      community.general.snap:
        name:
          - android-studio
        classic: true
    """

    server.user(
        name=f"Add {user} to kvm group",
        user=user,
        groups=["kvm"],
        append=True,
        _sudo=True,
    )

    """
    SETUP proxies

    - name: add dart proxy
      ansible.builtin.template:
        src: "dart-proxy.j2"
        dest: "~/bin/dart"
        mode: "u=rwx,go=rx"

    - name: add flutter proxy
      ansible.builtin.template:
        src: "flutter-proxy.j2"
        dest: "~/bin/flutter"
        mode: "u=rwx,go=rx"
   """


if basic_utils["enable_openvpn_config_import_network_manager"]:
    apt.packages(
        name="Install openvpn packages",
        packages=["network-manager-openvpn", "network-manager-openvpn-gnome"],
        _sudo=True,
    )

if basic_utils["enable_zoom"]:
    local.include(f"{DEPLOYS_DIR}/flatpak/deploy.py")
    flatpak.packages(packages=["us.zoom.Zoom"])

if basic_utils["enable_go"]:
    """
    TODO
    goenv_bin = f"{homebrew_binaries_path}/goenv"

    server.shell(
        name="Install goenv via brew",
        commands=[f"/home/{user}/bin/brew install goenv"],
        _if=lambda: host.get_fact(File, goenv_bin) is None,
    )
    """

    files.block(
        name="Setup goenv for bash",
        path=f"/home/{user}/.bashrc",
        marker="# {mark} ANSIBLE MANAGED BLOCK: add goenv",
        content="""\
export GOENV_ROOT="$HOME/.goenv"
eval "$($HOME/.goenv/bin/goenv init -)"\
""",
        try_prevent_shell_expansion=True,
    )

    if zsh_enabled:
        files.block(
            name="Setup goenv for zsh",
            path=f"/home/{user}/.zshrc",
            marker="# {mark} ANSIBLE MANAGED BLOCK: add goenv",
            content="""\
export GOENV_ROOT="$HOME/.goenv"
export PATH="$GOENV_ROOT/bin:$PATH"
eval "$($HOME/.goenv/bin/goenv init -)"\
""",
            try_prevent_shell_expansion=True,
        )

"""
TODO
- name: Add setup for bat
  when: "'bat' in ansible_facts.packages"
  block:
    - name: Create a symbolic link for bat
      ansible.builtin.file:
        src: "/usr/bin/batcat"
        dest: "/home/{{ user }}/bin/bat"
        state: link
"""
