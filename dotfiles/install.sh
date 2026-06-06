set -e

DOTFILES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ ! -d "$DOTFILES_DIR/.git" ]; then
    git init "$DOTFILES_DIR"
fi

mkdir -p "$HOME/.config/shell"
mkdir -p "$HOME/.bashrc.d"
mkdir -p "$HOME/.bash_aliases.d"
mkdir -p "$HOME/.zshrc.d"

link_file() {
    local src="$1"
    local dest="$2"
    if [ -e "$dest" ] || [ -L "$dest" ]; then
        rm -f "$dest"
    fi
    ln -sf "$src" "$dest"
}

link_file "$DOTFILES_DIR/.bash_aliases" "$HOME/.bash_aliases"

for file in "$DOTFILES_DIR"/.bashrc.d/*; do
    if [ -f "$file" ]; then
        link_file "$file" "$HOME/.bashrc.d/$(basename "$file")"
    fi
done

for file in "$DOTFILES_DIR"/.bash_aliases.d/*; do
    if [ -f "$file" ]; then
        link_file "$file" "$HOME/.bash_aliases.d/$(basename "$file")"
    fi
done

for file in "$DOTFILES_DIR"/.zshrc.d/*; do
    if [ -f "$file" ]; then
        link_file "$file" "$HOME/.zshrc.d/$(basename "$file")"
    fi
done

if [ -f "$HOME/.bashrc" ]; then
    if ! grep -q "source $DOTFILES_DIR/.bashrc" "$HOME/.bashrc"; then
        echo -e "\nsource $DOTFILES_DIR/.bashrc" >> "$HOME/.bashrc"
    fi
fi

if [ -f "$HOME/.zshrc" ]; then
    if ! grep -q "source $DOTFILES_DIR/.zshrc" "$HOME/.zshrc"; then
        echo -e "\nsource $DOTFILES_DIR/.zshrc" >> "$HOME/.zshrc"
    fi
fi
