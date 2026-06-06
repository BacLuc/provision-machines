export HISTSIZE=9999
export SAVEHIST=9999
DISABLE_MAGIC_FUNCTIONS=true
export PATH="/snap/bin:$PATH"
export PATH="$HOME/bin:$HOME/.local/bin:$PATH"

if [ -f ~/.bash_aliases ]; then
    source ~/.bash_aliases
fi

if [ -d ~/.zshrc.d ]; then
    for rc in ~/.zshrc.d/*; do
        [ -f "$rc" ] && source "$rc"
    done
fi
