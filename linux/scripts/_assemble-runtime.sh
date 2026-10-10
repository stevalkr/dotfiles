#!/usr/bin/env bash
set -euo pipefail

[[ "${1:-}" == -h || "${1:-}" == --help || "${1:-}" == help ]] && {
    printf '%s\n' 'Usage: _assemble-runtime.sh ENVIRONMENT-ROOT'
    exit 0
}
[[ $# == 1 && -d "$1/view" ]] || { printf '%s\n' 'Usage: _assemble-runtime.sh ENVIRONMENT-ROOT' >&2; exit 2; }
script_dir="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
root="$(CDPATH= cd -- "$1" && pwd)"
mkdir -p "$root/bin" "$root/etc/fonts"
install -m 0644 "$script_dir/activate.sh" "$root/activate.sh"
install -m 0755 "$script_dir/runtime-bin/wezterm" "$root/bin/wezterm"
install -m 0644 "$script_dir/../config/fontconfig.conf" "$root/etc/fonts/fonts.conf"
"$script_dir/_public-bin.sh" "$root"
