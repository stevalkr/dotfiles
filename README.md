# Dotfiles

GNU Stow manages `home/`; Homebrew provisions macOS. Linux requires Fish,
Fisher, Stow, and the applications used by the configs to be installed separately.

```sh
./bootstrap
./macos/test  # macOS only
```

Use `./bootstrap --enable-remote-login` to enable macOS Remote Login.
Bootstrap initializes submodules, installs macOS dependencies and Neovim
runtimes, applies macOS settings, and stows the configs.

Each run snapshots managed `~/.config/<application>` trees and macOS
`.zprofile` under `~/.dotfiles-backup/`. SSH configs receive adjacent `.bak`
files. Configs are replaced from the repository; previous runtime state is
not restored. Fisher reinstalls plugins from `fish_plugins` into
`~/.config/fish/fisher`. Fish startup does not update plugins.

To restow configs without provisioning or resetting state:

```sh
stow --restow --no-folding --dir "$PWD" --target "$HOME" home
stow --restow --no-folding --dir "$PWD/macos" --target "$HOME" home  # macOS only
```

To review and remove Homebrew packages outside the Brewfile:

```sh
brew bundle cleanup --file macos/Brewfile
brew bundle cleanup --force --file macos/Brewfile
```

Neovim's Python provider and Node tools live under
`${XDG_DATA_HOME:-~/.local/share}/nvim`. Only Neovim adds its Node runtime to
`PATH`. Notebook kernels belong to their project environments; register one
with:

```sh
uv pip install --python "$VIRTUAL_ENV/bin/python" ipykernel
"$VIRTUAL_ENV/bin/python" -m ipykernel install --user \
  --name "$(basename "$VIRTUAL_ENV")" \
  --display-name "Python ($(basename "$VIRTUAL_ENV"))"
```
