import io

from pyinfra import host
from pyinfra.operations import apt, files

user = host.data.get("user", "ubuntu")

if host.data.tmux["enabled"]:
    apt.packages(
        name="Install tmux",
        packages=["tmux"],
        _sudo=True,
    )

    default_shell = "/bin/zsh" if host.data.zsh["enabled"] else "/bin/bash"

    tmux_conf = (
        f"set-option -g default-shell {default_shell}\n"
        "\n"
        'set -g default-terminal "tmux-256color"\n'
        "\n"
        "set -g mouse on\n"
        "\n"
        "set-option -g history-limit 30000\n"
        "set-option -g bell-action current\n"
        "set-option -g visual-bell on\n"
        "\n"
        'bind r source-file ~/.tmux.conf \\; display "Config reloaded!"\n'
        "\n"
        "bind-key -T copy-mode MouseDragEnd1Pane  send-keys -X copy-pipe\n"
        "bind-key -T copy-mode C-w send-keys -X copy-pipe\n"
        "\n"
        'bind \'"\' split-window -v -c "#{pane_current_path}"\n'
        "bind % split-window -h -c \"#{pane_current_path}\"\n"
        "bind c new-window -c \"#{pane_current_path}\"\n"
        "\n"
        "set-window-option -g aggressive-resize on\n"
        "\n"
        "set-window-option -g monitor-activity off\n"
        "set-option -g visual-activity off\n"
        "\n"
        "set-window-option -g window-status-current-style bg=red\n"
        "\n"
        "set -g base-index 1\n"
        "\n"
        "set -g history-limit 30000\n"
        "\n"
        "set -g alternate-screen on\n"
        "\n"
        "set -s escape-time 100\n"
        "\n"
        "set-option -g status-justify left\n"
        "set-option -g status-left '#[bg=colour72] #[bg=colour237] #[bg=colour236] #[bg=colour235]#[fg=colour185] #S #[bg=colour236] '\n"
        "set-option -g status-left-length 16\n"
        "set-option -g status-bg colour237\n"
        "set-option -g status-right '#[bg=colour236] #[bg=colour235]#[fg=colour185] %a %R #[bg=colour236]#[fg=colour3] #[bg=colour237] #[bg=colour72] #[]'\n"
        "set-option -g status-interval 60\n"
        "\n"
        "set-option -g pane-active-border-style fg=colour246\n"
        "set-option -g pane-border-style fg=colour238\n"
        "\n"
        "set-window-option -g window-status-format '#[bg=colour238]#[fg=colour107] #I #[bg=colour239]#[fg=colour110] #[bg=colour240]#W#[bg=colour239]#[fg=colour195]#F#[bg=colour238] '\n"
        "set-window-option -g window-status-current-format '#[bg=colour236]#[fg=colour215] #I #[bg=colour235]#[fg=colour167] #[bg=colour234]#W#[bg=colour235]#[fg=colour195]#F#[bg=colour236] '\n"
        "\n"
        "set-option -g automatic-rename on\n"
        "set-option -g automatic-rename-format \"#{b:pane_current_path} #{pane_current_command}\"\n"
    )

    files.put(
        name="Add tmux config",
        src=io.StringIO(tmux_conf),
        dest=f"/home/{user}/.tmux.conf",
        mode="644",
    )
