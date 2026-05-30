import io

from pyinfra import host
from pyinfra.operations import apt, files

from operations.user import get_user_name

user = get_user_name()

if host.data.tmux["enabled"]:
    apt.packages(
        name="Install tmux",
        packages=["tmux"],
        _sudo=True,
    )

    default_shell = "/bin/zsh" if host.data.zsh["enabled"] else "/bin/bash"

    tmux_conf = f"""# Terminal behaviour
set-option -g default-shell {default_shell}

set -g default-terminal "tmux-256color"

set -g mouse on

set-option -g history-limit 30000
set-option -g bell-action current
set-option -g visual-bell on

bind r source-file ~/.tmux.conf \\; display "Config reloaded!"

bind-key -T copy-mode MouseDragEnd1Pane  send-keys -X copy-pipe
bind-key -T copy-mode C-w send-keys -X copy-pipe

bind '"' split-window -v -c "#{{pane_current_path}}"
bind % split-window -h -c "#{{pane_current_path}}"
bind c new-window -c "#{{pane_current_path}}"

set-window-option -g aggressive-resize on

set-window-option -g monitor-activity off
set-option -g visual-activity off

set-window-option -g window-status-current-style bg=red

set -g base-index 1

set -g history-limit 30000

set -g alternate-screen on

set -s escape-time 100

set-option -g status-justify left
set-option -g status-left '#[bg=colour72] #[bg=colour237] #[bg=colour236] #[bg=colour235]#[fg=colour185] #S #[bg=colour236] '
set-option -g status-left-length 16
set-option -g status-bg colour237
set-option -g status-right '#[bg=colour236] #[bg=colour235]#[fg=colour185] %a %R #[bg=colour236]#[fg=colour3] #[bg=colour237] #[bg=colour72] #[]'
set-option -g status-interval 60

set-option -g pane-active-border-style fg=colour246
set-option -g pane-border-style fg=colour238

set-window-option -g window-status-format '#[bg=colour238]#[fg=colour107] #I #[bg=colour239]#[fg=colour110] #[bg=colour240]#W#[bg=colour239]#[fg=colour195]#F#[bg=colour238] '
set-window-option -g window-status-current-format '#[bg=colour236]#[fg=colour215] #I #[bg=colour235]#[fg=colour167] #[bg=colour234]#W#[bg=colour235]#[fg=colour195]#F#[bg=colour236] '

set-option -g automatic-rename on
set-option -g automatic-rename-format "#{{b:pane_current_path}} #{{pane_current_command}}"
"""

    files.put(
        name="Add tmux config",
        src=io.StringIO(tmux_conf),
        dest=f"/home/{user}/.tmux.conf",
        user=user,
        group=user,
        mode="644",
    )
