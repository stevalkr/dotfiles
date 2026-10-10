from spack_repo.builtin.packages.tmux.package import Tmux as BuiltinTmux

from spack.package import *


class Tmux(BuiltinTmux):
    version("3.7c", sha256="7c60cae9a0e25288e2e24750aafc9e8800fc7fd4555e447e1b29ee4201cfb3bf")
