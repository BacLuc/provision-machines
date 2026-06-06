if command -v kubectl >/dev/null 2>&1; then
    source <(kubectl completion zsh)
    complete -F __start_kubectl k
    [[ $commands[kubectl] ]] && source <(kubectl completion zsh)
fi
