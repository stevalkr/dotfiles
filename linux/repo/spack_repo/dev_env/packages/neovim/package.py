from spack_repo.builtin.packages.neovim.package import Neovim as BuiltinNeovim

from spack.package import *


class Neovim(BuiltinNeovim):
    """Exact nightly selected by the pinned neovim-nightly overlay snapshot."""

    version(
        "0.13.0-dev.20260922",
        url="https://github.com/neovim/neovim/archive/51d7d99fe7c3625f524b47f3f5d041c6a5895f81.tar.gz",
        sha256="a612172a85ca93957c3a50ada413c72fa07d016a57e35c0814737e1dd60d40ee",
    )
