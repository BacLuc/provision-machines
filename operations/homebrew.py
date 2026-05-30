HOMEBREW_HOME = "/home/linuxbrew"
HOMEBREW_LINUXBREW = f"{HOMEBREW_HOME}/.linuxbrew"
HOMEBREW_BIN = f"{HOMEBREW_LINUXBREW}/bin"
HOMEBREW_BREW_BIN = f"{HOMEBREW_BIN}/brew"
HOMEBREW_CELLAR = f"{HOMEBREW_LINUXBREW}/Cellar"


def user_brew_bin(user: str) -> str:
    return f"/home/{user}/bin/brew"
