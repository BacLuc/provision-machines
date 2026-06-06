if command -v fzf >/dev/null 2>&1; then
    FZF_DEFAULT_OPTS="--tmux"
    source <(fzf --zsh)
fi
