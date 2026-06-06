# renovate: datasource=docker depName=ghcr.io/bacluc/prettier-image/prettier-image
bash_prettier_image_version="3.8.1"

alias ll='ls -lhA --color=auto'
alias cdp='cd $(pwd)'
alias bigdirs='du --human-readable --max-depth=1 2> /dev/null | sort --human-numeric-sort -r | head -n20'
alias prettier="docker run --rm -v \$PWD:/workdir -w /workdir -u \$UID ghcr.io/bacluc/prettier-image/prettier-image:\${bash_prettier_image_version}"
alias dc='docker compose'
alias goto='cd $(find ~ -type d | fzf)'
alias k=kubectl
alias ka='kubectl --as "system:admin"'
alias kn='f() { [ "$1" ] && kubectl config set-context --current --namespace $1 || kubectl config view --minify | grep namespace | cut -d" " -f6 ; } ; f'
alias helma='helm --kube-as-user "system:admin"'
alias kgworld='kubectl get $(kubectl api-resources --verbs=list --namespaced -o name | paste -sd ",")'
alias kagworld='kubectl --as "system:admin" get $(kubectl api-resources --verbs=list --namespaced -o name | paste -sd ",")'
alias k9sa='k9s --as "system:admin"'
alias kl='kharon oc-web-login'
