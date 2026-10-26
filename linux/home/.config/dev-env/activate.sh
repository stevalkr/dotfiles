# shellcheck shell=bash
# Source from ~/.bashrc. Everything goes through the current-release link, so
# switching releases needs no change here. No-op until ./linux/install runs.

if [[ -d "$HOME/.local/share/dev-env/public/bin" ]]; then
    _dev_env=$HOME/.local/share/dev-env

    _dev_env_prepend() { # _dev_env_prepend <variable> <directory> [default]
        local current=":${!1:-${3:-}}:"
        current=${current//":$2:"/:}
        current=${current#:}
        current=${current%:}
        printf -v "$1" '%s' "$2${current:+:$current}"
        export "${1?}"
    }

    _dev_env_prepend PATH "$_dev_env/public/bin"
    # Wrappers (nvim, wezterm) shadow the public commands.
    _dev_env_prepend PATH "$HOME/.local/bin"
    _dev_env_prepend XDG_DATA_DIRS "$_dev_env/view/share" /usr/local/share:/usr/share
    _dev_env_prepend TERMINFO_DIRS "$_dev_env/view/share/terminfo"
    # An empty entry keeps the system terminfo.
    case ":$TERMINFO_DIRS:" in *::*) ;; *) TERMINFO_DIRS+=: ;; esac
    export DISABLE_AUTOUPDATER=1

    unset -f _dev_env_prepend
    unset _dev_env
fi
