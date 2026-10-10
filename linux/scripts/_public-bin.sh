#!/usr/bin/env bash
set -euo pipefail

usage() {
    printf 'Usage: _public-bin.sh <environment-root>\n'
}

case "${1:-}" in
    -h|--help|help)
        usage
        exit 0
        ;;
esac

if (($# != 1)); then
    usage >&2
    exit 2
fi

root="$(CDPATH= cd -- "$1" && pwd)"
# This is intentionally an allowlist.  In particular, Python, Node.js, their
# package managers, and generic language-environment entry points stay private
# to the Spack view. Neovim's launcher gives only its own process tree access
# to the provider paths and bundled interpreter commands.
public_tools=(
    bat
    bwrap
    clang
    clang++
    clang-format
    clang-tidy
    clangd
    cmake-format
    cmake-lint
    direnv
    codespell
    fd
    fish
    fzf
    jupytext
    jupytext-config
    ld.lld
    lld
    llvm-ar
    llvm-nm
    llvm-objdump
    llvm-readelf
    magick
    markdownlint
    pyink
    prettierd
    pyright
    pyright-langserver
    rg
    stow
    zoxide
    rocketchat-tui
    tmux
    tree-sitter
)

mkdir -p "$root/bin"
for tool in "${public_tools[@]}"; do
    target="$root/view/bin/$tool"
    if [[ ! -x "$target" ]]; then
        printf 'public-bin: required command is missing: %s\n' "$target" >&2
        exit 1
    fi
done

for tool in "${public_tools[@]}"; do
    case "$tool" in
        markdownlint|prettierd|pyright|pyright-langserver)
            rm -f -- "$root/bin/$tool"
            install -m 0755 "$(dirname -- "${BASH_SOURCE[0]}")/runtime-bin/node-tool" "$root/bin/$tool"
            ;;
        *) ln -sfn "../view/bin/$tool" "$root/bin/$tool" ;;
    esac
done

for private in python python3 node npm npx corepack neovim-node-host; do
    if [[ -e "$root/bin/$private" || -L "$root/bin/$private" ]]; then
        printf 'public-bin: private interpreter command leaked into bin: %s\n' \
            "$private" >&2
        exit 1
    fi
done
