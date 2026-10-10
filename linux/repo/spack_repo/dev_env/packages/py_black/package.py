from spack_repo.builtin.packages.py_black.package import PyBlack as BuiltinPyBlack

from spack.package import *


class PyBlack(BuiltinPyBlack):
    """Matching Black library version required by Pyink 26.5.1."""

    version("26.5.1", sha256="dd321f668053961824bcc1be1cc1df748b2d7e4fa28086b08331e577b0100a73")
