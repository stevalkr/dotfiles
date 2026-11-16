from spack_repo.builtin.packages.zoxide.package import Zoxide as BuiltinZoxide

from spack.package import *


class Zoxide(BuiltinZoxide):
    """Builtin zoxide; 0.9.9+ reads fish's embedded cd instead of $__fish_data_dir."""

    version("0.10.0", sha256="4fcd4272b013a10b637dbcc299c58a9924b94470a9042677ca1a204cc2e9150e")

    depends_on("rust@1.88:", type="build", when="@0.10:")
