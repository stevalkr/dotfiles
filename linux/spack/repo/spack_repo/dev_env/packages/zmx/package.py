import os

from spack_repo.builtin.build_systems.generic import Package

from spack.package import *


class Zmx(Package):
    """Session attach/detach for the terminal, installed from the static release binary."""

    homepage = "https://github.com/neurosnap/zmx"
    url = "https://zmx.sh/a/zmx-0.8.1-linux-x86_64.tar.gz"

    license("MIT")

    # Upstream builds require Zig 0.16 and a pinned Ghostty checkout; the
    # release binary is statically linked, so it runs on the EL8 baseline.
    version("0.8.1", sha256="dfd75720b942466f28870731cc86dbc07afa72fb8f3bd5eeb4ff707e4eecebe8")

    def install(self, spec, prefix):
        mkdirp(prefix.bin)
        install("zmx", prefix.bin)

        zmx = Executable(prefix.bin.zmx)
        completions = {
            "bash": join_path(prefix.share, "bash-completion", "completions", "zmx"),
            "zsh": join_path(prefix.share, "zsh", "site-functions", "_zmx"),
            "fish": join_path(prefix.share, "fish", "vendor_completions.d", "zmx.fish"),
        }
        for shell, path in completions.items():
            mkdirp(os.path.dirname(path))
            with open(path, "w") as stream:
                zmx("completions", shell, output=stream)
