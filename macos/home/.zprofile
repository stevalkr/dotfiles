if [[ -x /opt/homebrew/bin/brew ]]; then
  eval "$(/opt/homebrew/bin/brew shellenv zsh)"
fi

typeset -U path
path=("$HOME/.local/bin" $path)
export PATH
