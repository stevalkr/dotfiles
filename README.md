# Dotfiles

Keep the checkout at a permanent path. Run commands from its root.

## macOS

Requires Apple Silicon, Homebrew at `/opt/homebrew`, and internet access.

```sh
git submodule update --init --recursive
./bootstrap
nvim # Wait for plugin/parser installation, then quit.
```

To enable Remote Login, use `./bootstrap --enable-remote-login`.
Change packages in `macos/Brewfile`, then rerun `./macos/bootstrap`.

## Linux

Packages are built on a connected builder and installed on an offline server
(x86-64, glibc 2.28+). Configs are synced by hand and stowed by `./bootstrap`.

### Builder

Requires Docker with `linux/amd64` support, Git, Bash, Python 3, GNU tar,
coreutils, and zstd. To use another machine, sync the checkout to it; keep its
`linux/out/` there:

```sh
git submodule update --init --recursive
rsync -a --delete --exclude /linux/out/ ./ builder:~/dotfiles/
ssh -t builder
cd ~/dotfiles
```

```sh
./linux/build    # build packages and release files
./linux/prepare  # only when Neovim data must change; quit nvim after its builds
./linux/bundle   # full archive in linux/out/bundle/
./linux/bundle --base <id>  # only what the server's release <id> lacks
./linux/bundle --list       # recorded ids
```

`prepare` updates `home/.config/nvim/nvim-pack-lock.json`; commit it in the
submodule.

`prepare` starts from an empty container home each run, so plugins are cloned
again; rerun it if the network cuts it short.

`build` and `prepare` pass `HTTP_PROXY`/`HTTPS_PROXY`/`NO_PROXY` to their
containers.

Copy the archive and the checkout (without `linux/out/`) to the server.

### Server

Requires Linux x86-64, glibc 2.28+, a non-root user, Bash, Python 3.6+, GNU tar,
coreutils, findutils, and zstd.

```sh
./linux/unbundle /path/to/dev-env-<id>.tar
./linux/install       # newest release; or ./linux/install <id>
./bootstrap
```

Add this line to `~/.bashrc`:

```sh
source "$HOME/.config/dev-env/activate.sh"
```

`./bootstrap` links `~/.local/state/nvim` (undo, ShaDa, swap) to
`linux/out/state/nvim`, shared by every machine on the checkout; the first
machine's existing state seeds it. `~/.local/share/nvim` links to the current
release's Neovim data, which `./linux/install` extracts once per release.

To revert, install the older release; Neovim data follows it:

```sh
./linux/install <id>
```

To keep only the current release (or `<id>`) and free space, run
`./linux/compact [<id>]`. Also run it after a Spack update. Later incremental
bundles must use the kept release as their base.

On the builder, `rm -rf linux/out/cache` frees space; the next build reuses
`linux/out/dist/`.

To relink configs only (no packages or backups), use `./bootstrap --stow-only`
(on Linux, after `./linux/install`).

