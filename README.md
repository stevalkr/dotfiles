# Dotfiles

GNU Stow manages shared configuration in `home/` and platform configuration in
`macos/home/` or `linux/home/`. Homebrew provisions macOS; the [Linux workflow](linux/README.md)
builds portable packages and prepares runtime data for offline servers.

For connected macOS provisioning:

```sh
./bootstrap
./macos/test
```

Use `./bootstrap --enable-remote-login` to enable macOS Remote Login. Bootstrap
initializes submodules, installs Homebrew dependencies and Neovim runtimes,
prepares Fisher, applies macOS settings, backs up managed configuration, and
stows it. Config snapshots go under `~/.dotfiles-backup/`; SSH configs receive
adjacent `.bak` files.

To activate or restow configuration on either platform:

```sh
./activate
```

Activation is offline: it only runs Stow. Populate submodules before transferring
the complete checkout. On Linux, install packages and restore runtime data first,
then source the installed prefix's `activate.sh` to make Stow available.

Platform Neovim wrappers in `~/.local/bin` select providers before `init.lua` runs.
macOS providers and Node tools live under `${XDG_DATA_HOME:-~/.local/share}/nvim`;
Linux uses its activated package prefix. Private interpreter paths are added to
Neovim's process environment. Fisher plugins and management data live under
`${XDG_DATA_HOME:-~/.local/share}/fisher`; Fish startup does not update plugins.
Connected macOS provisioning moves the former `.config/fish/fisher` installation
to that location. To refresh Fisher on a connected machine, run
`./scripts/prepare-fisher`.

```sh
uv pip install --python "$VIRTUAL_ENV/bin/python" ipykernel
"$VIRTUAL_ENV/bin/python" -m ipykernel install --user \
  --name "$(basename "$VIRTUAL_ENV")" \
  --display-name "Python ($(basename "$VIRTUAL_ENV"))"
```

To review or remove Homebrew packages outside the Brewfile:

```sh
brew bundle cleanup --file macos/Brewfile
brew bundle cleanup --force --file macos/Brewfile
```
