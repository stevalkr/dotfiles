#!/usr/bin/env bash

_dev_env_activate_dir="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if [[ -d "$_dev_env_activate_dir/view" ]]; then
    DEV_ENV_ROOT="$_dev_env_activate_dir"
elif [[ -d "$_dev_env_activate_dir/../view" ]]; then
    DEV_ENV_ROOT="$(CDPATH= cd -- "$_dev_env_activate_dir/.." && pwd)"
else
    printf 'dev-env: no environment view next to %s\n' "${BASH_SOURCE[0]}" >&2
    unset _dev_env_activate_dir
    return 2 2>/dev/null || exit 2
fi
export DEV_ENV_ROOT

_dev_env_prepend_path() {
    case ":${PATH:-}:" in
        *":$1:"*) ;;
        *) PATH="$1${PATH:+:$PATH}" ;;
    esac
}

_dev_env_prepend_path "$DEV_ENV_ROOT/bin"
# The Stow wrapper selects Neovim providers before init.lua runs.
PATH="$HOME/.local/bin${PATH:+:$PATH}"
export PATH

# Expose packaged application data without replacing existing XDG locations.
case ":${XDG_DATA_DIRS:-}:" in
    *":$DEV_ENV_ROOT/view/share:"*) ;;
    *) XDG_DATA_DIRS="$DEV_ENV_ROOT/view/share:${XDG_DATA_DIRS:-/usr/local/share:/usr/share}" ;;
esac
export XDG_DATA_DIRS

if [[ -d "$DEV_ENV_ROOT/view/share/terminfo" ]]; then
    case ":${TERMINFO_DIRS:-}:" in
        *":$DEV_ENV_ROOT/view/share/terminfo:"*) ;;
        *) TERMINFO_DIRS="$DEV_ENV_ROOT/view/share/terminfo:${TERMINFO_DIRS:-}" ;;
    esac
    export TERMINFO_DIRS
fi

if [[ -f "$DEV_ENV_ROOT/etc/fonts/fonts.conf" ]]; then
    export FONTCONFIG_FILE="$DEV_ENV_ROOT/etc/fonts/fonts.conf"
fi

unset -f _dev_env_prepend_path
unset _dev_env_activate_dir
