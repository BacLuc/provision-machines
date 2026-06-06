export HISTSIZE=9999
export HISTFILESIZE=99999
export LS_COLORS='di=0;35'
export PATH="/snap/bin:$PATH"
export PATH="$HOME/bin:$HOME/.local/bin:$PATH"

if [ -f /usr/share/autojump/autojump.sh ]; then
    source /usr/share/autojump/autojump.sh
fi

if [ -f ~/.bash_aliases ]; then
    source ~/.bash_aliases
fi

if [ -d ~/.bashrc.d ]; then
    for rc in ~/.bashrc.d/*; do
        [ -f "$rc" ] && source "$rc"
    done
fi

if [ -d ~/.bash_aliases.d ]; then
    for rc in ~/.bash_aliases.d/*; do
        [ -f "$rc" ] && source "$rc"
    done
fi
