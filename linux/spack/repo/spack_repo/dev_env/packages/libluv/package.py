from spack_repo.builtin.packages.libluv.package import Libluv as BuiltinLibluv

from spack.package import *


class Libluv(BuiltinLibluv):
    """The luv release Neovim's own build pins."""

    version("1.52.1-0", sha256="3e6eb820a3aee034f85f9cce9bd77b5d42f34d128a1ccec877adf28c913577c7")
