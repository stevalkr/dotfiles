# Portable Linux packages

The initial target is Linux x86-64, glibc 2.28 or newer, installed as a non-root
user. Builds use the pinned Rocky Linux 8.7 image and GCC 8.5.0. The target needs
Bash, Python 3, GNU tar/coreutils, and zstd; Bubblewrap also needs unprivileged
user namespaces. WezTerm GUI use needs the host's display and GPU stack.

Packages, Stow configuration, and prepared runtime data are independent.
Installation accepts a **new prefix**. For an update, reuse the transferred
binary mirror, install into another prefix, and switch activation after success.
Existing installations and older mirror objects are retained.

## Connected workflow

The host needs Docker with `linux/amd64` support, Git, Bash, Python 3, GNU checksum
tools, zstd for local-data packing, and space/memory to build LLVM and WezTerm.

```sh
git submodule update --init --recursive
./linux/build
./linux/pack
./linux/local-prepare
./linux/local-pack
```

`build` obtains pinned Spack sources under `linux/out/sources`, concretizes into
`linux/out/spack/spack.lock`, installs the environment, and applies the demonstrated
LLVM RPATH repair. It does not pack packages. Generated caches, stores, views,
logs, and artifacts stay under ignored `linux/out/`. Source changes invalidate the
builder image and require a new build before packing.

`pack` exports the complete locked graph, including build dependencies, to a
persistent unsigned binary mirror. It bundles pinned Spack sources, recipes,
the concrete lockfile, and offline bootstrap resources in a metadata archive.
Checksums cover the archive and all mirror files:

```text
linux/out/packages/
  metadata.tar.zst
  mirror/
  SHA256SUMS
```

`local-prepare` runs in the connected EL8 preparation container, installs packages,
stows the complete mounted checkout, and populates Neovim plugins, parsers,
native Blink assets, and remote-plugin registration. Fisher and Fish plugin files
are already part of the shared configuration and are installed by Stow.
The isolated home persists at `linux/out/test-home`; the checkout is mounted
read-only except for a writable preparation copy of the Neovim config lockfile
at `linux/out/nvim-pack-lock.json`. Neovim uses its normal config lockfile and
plugin behavior. Wait for plugin/parser builds to finish in the interactive
Neovim session, then quit; preparation checks the resulting assets.

After changing plugins, copy the prepared lock back before transferring the
dotfiles snapshot:

```sh
cp linux/out/nvim-pack-lock.json home/.config/nvim/nvim-pack-lock.json
```

To prepare from a newly edited config lock instead, replace
`linux/out/nvim-pack-lock.json` with that file before starting the container.

`local-pack` creates `linux/out/local/linux-local.tar.zst` and its checksum.
It requires the Linux preparation marker and archives only `.local/share/nvim`. Stow wrappers/configs, provider environments, session
files, and logs are excluded. Native assets and plugin Git metadata are retained.
Remote-plugin registration uses the target's `$HOME`.
An alternate preparation home can be supplied to `local-pack`.

For an interactive connected preparation shell:

```sh
./linux/test
# inside the container, to repeat preparation:
/opt/dotfiles/linux/local-prepare
```

The test entrypoint reuses a matching installation. If package selection changed,
choose a new prefix:

```sh
LINUX_TEST_PREFIX=/home/tester/another/prefix ./linux/test
```

The same build and pack scripts can run over SSH: copy the complete checkout to
the builder, run the commands there, and copy artifacts back. No remote-build or
umbrella command is required.

## Offline deployment

Transfer the package input directory, runtime archive and checksum, and a complete
dotfiles snapshot with populated submodules. Include local plugin submodules;
exclude generated build state when copying dotfiles. Keep the package directory
on the target to reuse unchanged cache objects later.

```sh
./linux/install "$HOME/opt/dev-env-1" /transfer/packages
source "$HOME/opt/dev-env-1/activate.sh"
./linux/local-install /transfer/linux-local.tar.zst
./bootstrap
```

Package installation checks compatibility/checksums and installs from the local
mirror with `--use-buildcache=only` and all packages marked non-buildable. It never
concretizes on the target. Failure removes the newly created prefix; retry the
same command. An existing installation is not replaced. Activation resources and
public launchers are generated after installation succeeds. The prefix records
its transferred mirror path; keep that cache in place for future installations.

`local-install` verifies and merges runtime data into `$HOME`, or a home supplied
as its second argument. It does not install packages or stow config. Back up
runtime data before replacing an existing prepared environment. This workflow
uses the default XDG paths; Linux data is prepared separately from macOS providers.
Linux bootstrap backs up existing managed configs under `~/.dotfiles-backup/`
and SSH configs in adjacent `.bak` files before Stow, without network access.

The prefix's `activate.sh` exposes curated commands/application data, with
`~/.local/bin` first. Python, Node, and package managers stay private. The Linux
Neovim wrapper invokes `$DEV_ENV_ROOT/view/bin/nvim` explicitly and sets providers
before initialization. Public Node tools use their bundled Node launcher too.

## Transfer only changed packages

After a version change, rebuild and pack. Unchanged mirror object filenames stay
stable. Copy changed/new mirror files, including metadata/index files, and the new
`metadata.tar.zst`. Copy `SHA256SUMS` last. Keep previously transferred files; there
is no base-release matching, delta format, or automatic pruning. One changed root
can change several dependency/cache files.

For example, with a transfer connection, rsync can select changed files:

```sh
rsync -a --checksum --exclude SHA256SUMS linux/out/packages/ server:/transfer/packages/
rsync -a linux/out/packages/SHA256SUMS server:/transfer/packages/
```

An offline server can use removable media and the same file selection. Then:

```sh
./linux/install "$HOME/opt/dev-env-2" /transfer/packages
source "$HOME/opt/dev-env-2/activate.sh"
```

This installs the desired set into a new prefix from already transferred files;
it does not require retransferring unchanged binaries. Configuration and local
data can be updated independently.

## Package inputs

Selections are in `spack.yaml`; Spack, package-repository, platform, and base-image
pins are in `config/spack-pins.env`. Recipes add unavailable versions, offline
Cargo/npm/Go resources, and necessary portability fixes.

Neovim uses commit `51d7d99fe7c3625f524b47f3f5d041c6a5895f81`;
Tree-sitter uses `baad4174e551e527bde1b069f4b41082e4abd085`. These tested development
pins are retained. WezTerm uses the reviewed development commit
[`372548295b0b25c9a5400f0ea56f0e89f47e0524`](https://github.com/wezterm/wezterm/commit/372548295b0b25c9a5400f0ea56f0e89f47e0524)
from October 5, 2026. Its crates.io resources were regenerated from Cargo.lock;
both Git dependencies and source submodules are pinned. Obsolete patches for
`time 0.3.31` and Lua never-type fallback were removed. WezTerm requires Rust 1.88
or newer as a build dependency while retaining EL8. The prettierd recipe pins
0.29.0 and resolved npm resource checksums. `scripts/_generate-resources.py`
regenerates resource tables from upstream lockfiles.

The Python inventory retains pynvim, Jupyter client, nbformat, Pillow, CairoSVG,
pyperclip, Jupytext, Pyink, and codespell alongside private Node providers and
Pyright. It supports notebook kernels, raster/SVG output, and clipboard support.
Cairo is a native Spack dependency; its Python binding loads the relocated library
explicitly. Requests/websocket-client are not directly used by retained config;
transitive dependencies remain managed by Spack. Optional Molten Plotly and LaTeX
image conversion are not provisioned: they require an extra browser or TeX runtime.
Their text/image notebook alternatives remain available. macOS's broader Python
and Brewfile inventories stay intact.

Linux adds Stow, direnv, zoxide, cmakelang, and prettierd, and removes the duplicate
fzf-fish root. The shared config includes Fisher and Fish plugins. No explicit Git, curl, wget, gh, tree,
htop, or extra language-development roots are added. Build-only language toolchains
remain dependencies when selected applications need them.

## Manual verification

There is no automated offline acceptance suite. On the target, install at a prefix
different from preparation, restore data into a different home, stow the complete
config, and disable host networking. Exercise:

- Fish startup, fzf bindings, bass, direnv, and zoxide.
- Neovim editing, completion, highlighting/parsers, and remote plugins.
- Python/Node providers and registered project notebook kernels.
- Notebook raster/SVG images and ImageMagick.
- `markdownlint`, `prettierd`, and `pyright` from the activated shell.
- Clang, clangd, LLD, and OpenMP. System-header/linking use also needs the target's
  C library development headers/startup objects or a project sysroot.
- WezTerm CLI, fonts, and GUI where a compatible display is available.

Use `:checkhealth` to review provider/plugin results. Confirm `command -v nvim`
selects `~/.local/bin/nvim`. Review lockfile changes after updating plugins.
Copy changed package files for a second selection and install into a fresh prefix
while confirming that the old prefix still works.
