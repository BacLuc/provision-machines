#/bin/sh

set -e

user="{{ user }}"

su "$user" -c "/home/${user}/.oh-my-zsh/tools/upgrade.sh"
