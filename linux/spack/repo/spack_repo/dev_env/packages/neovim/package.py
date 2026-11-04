from spack_repo.builtin.packages.neovim.package import Neovim as BuiltinNeovim

from spack.package import *


class Neovim(BuiltinNeovim):
    """Exact nightly selected by the pinned neovim-nightly overlay snapshot."""

    version(
        "0.13.0-dev.20260922",
        url="https://github.com/neovim/neovim/archive/51d7d99fe7c3625f524b47f3f5d041c6a5895f81.tar.gz",
        sha256="a612172a85ca93957c3a50ada413c72fa07d016a57e35c0814737e1dd60d40ee",
    )

    # The LuaJIT from this commit's cmake.deps/deps.txt, which upstream tests;
    # packages.yaml makes it the luajit provider.
    depends_on("lua-luajit@=2.1.1788460057", when="@=0.13.0-dev.20260922")
    # luv 1.50.0-1, Spack's newest, breaks vim.async under :checkhealth.
    depends_on("libluv@=1.52.1-0", when="@=0.13.0-dev.20260922")
