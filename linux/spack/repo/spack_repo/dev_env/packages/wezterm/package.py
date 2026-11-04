import json

from spack_repo.builtin.build_systems.generic import Package

from spack.package import *
from spack_repo.dev_env._cargo_vendor import (
    _files_checksum, configure_crates_io_vendor, declare_crate_resources,
)
from spack_repo.dev_env.packages.wezterm.cargo_resources import CRATES


class Wezterm(Package):
    """GPU-accelerated terminal with both X11 and Wayland support."""

    homepage = "https://wezfurlong.org/wezterm/"
    git = "https://github.com/wezterm/wezterm.git"

    license("MIT")

    version(
        "20261005.3725482",
        commit="372548295b0b25c9a5400f0ea56f0e89f47e0524",
        submodules=True,
    )
    declare_crate_resources(resource, CRATES, "@=20261005.3725482")
    resource(
        name="xcb-imdkit",
        git="https://github.com/wezterm/xcb-imdkit-rs.git",
        commit="212330f7c6c37794d78061a773e8f4f9e4785bbb",
        submodules=True,
        placement=".spack-git/xcb-imdkit",
        when="@=20261005.3725482",
    )

    resource(
        name="finl-unicode",
        git="https://github.com/wez/finl_unicode.git",
        commit="a1892f26245529f2ef3877a9ebd610c96cec07a6",
        placement=".spack-git/finl-unicode",
        when="@=20261005.3725482",
    )

    depends_on("c", type="build")
    depends_on("cxx", type="build")
    depends_on("rust@1.88:", type="build")
    depends_on("pkgconfig", type="build")
    depends_on("perl", type="build")
    depends_on("ncurses", type=("build", "run"))
    depends_on("fontconfig")
    depends_on("freetype")
    depends_on("openssl")
    depends_on("zlib-api")
    depends_on("libxcb")
    depends_on("xcb-util")
    depends_on("xcb-util-image")
    depends_on("xcb-util-keysyms")
    depends_on("xcb-util-wm")
    depends_on("libxkbcommon+wayland")
    depends_on("xkeyboard-config", type="run")
    depends_on("wayland")
    depends_on("mesa+egl~llvm")

    phases = ["build", "install"]

    def setup_build_environment(self, env):
        env.set("CARGO_NET_OFFLINE", "true")

    def build(self, spec, prefix):
        # Without Git metadata in the stage, wezterm-version reads the version
        # from .tag; this is what upstream's `git show` would produce.
        if spec.satisfies("@=20261005.3725482"):
            with open(join_path(self.stage.source_path, ".tag"), "w") as stream:
                stream.write("20261005-054844-37254829\n")
        configure_crates_io_vendor(self.stage.source_path, CRATES)
        # Replace the source, not the dependency: Cargo.lock must retain its
        # exact Git identity when building with --locked --offline.
        git_root = join_path(self.stage.source_path, ".spack-git")
        for name in ("xcb-imdkit", "finl-unicode"):
            git_crate = join_path(git_root, name)
            with open(join_path(git_crate, ".cargo-checksum.json"), "w") as stream:
                json.dump({"files": _files_checksum(git_crate), "package": None}, stream)
        vendor_config = join_path(self.stage.source_path, ".cargo", "config.toml")
        with open(vendor_config, "a") as stream:
            stream.write(
                '\n[source.xcb-imdkit]\n'
                'git = "https://github.com/wezterm/xcb-imdkit-rs.git"\n'
                'rev = "212330f7c6c37794d78061a773e8f4f9e4785bbb"\n'
                'replace-with = "spack-git"\n\n'
                '[source.finl-unicode]\n'
                'git = "https://github.com/wez/finl_unicode.git"\n'
                'branch = "no_std"\nreplace-with = "spack-git"\n\n'
                '[source.spack-git]\ndirectory = ' + json.dumps(git_root) + '\n'
            )
        cargo(
            # Upstream also ships .cargo/config, which otherwise takes
            # precedence over our generated config.toml.
            "--config",
            vendor_config,
            "build",
            "--release",
            "--locked",
            "--offline",
            "-p",
            "wezterm-gui",
            "-p",
            "wezterm",
            "-p",
            "wezterm-mux-server",
            "-p",
            "strip-ansi-escapes",
        )

    def install(self, spec, prefix):
        mkdirp(prefix.bin)
        for executable in ("wezterm", "wezterm-gui", "wezterm-mux-server", "strip-ansi-escapes"):
            install(join_path("target", "release", executable), prefix.bin)
        install("assets/open-wezterm-here", prefix.bin)

        install_tree("assets/shell-integration", prefix.share.wezterm.shell_integration)
        mkdirp(bash_completion_path(prefix))
        install("assets/shell-completion/bash", bash_completion_path(prefix) / "wezterm")
        mkdirp(fish_completion_path(prefix))
        install("assets/shell-completion/fish", fish_completion_path(prefix) / "wezterm.fish")
        mkdirp(zsh_completion_path(prefix))
        install("assets/shell-completion/zsh", zsh_completion_path(prefix) / "_wezterm")

        mkdirp(prefix.share.applications)
        install("assets/wezterm.desktop", prefix.share.applications)
        mkdirp(prefix.share.metainfo)
        install("assets/wezterm.appdata.xml", prefix.share.metainfo)
        icon_dir = join_path(prefix.share.icons.hicolor, "128x128", "apps")
        mkdirp(icon_dir)
        install("assets/icon/terminal.png", join_path(icon_dir, "org.wezfurlong.wezterm.png"))

        terminfo = prefix.share.terminfo
        mkdirp(terminfo)
        tic = which(spec["ncurses"].prefix.bin.tic, required=True)
        tic("-x", "-o", terminfo, "termwiz/data/wezterm.terminfo")
