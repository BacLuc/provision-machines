#/bin/sh

set -e

homebrew_bin="{{ homebrew_path }}/brew"
user="{{ user }}"

export NONINTERACTIVE=1
su "$user" -c "${homebrew_bin} update"
su "$user" -c "${homebrew_bin} upgrade"
