from spack_repo.builtin.packages.lazygit.package import Lazygit as BuiltinLazygit

from spack.package import *


class Lazygit(BuiltinLazygit):
    # The source tree vendors its Go modules.
    version("0.66.3", sha256="49e80d28e03e53048105f6ebb5afefbe5caacffa8549347d8a59eab3a00dafe1")

    depends_on("go@1.26:", type="build", when="@0.66:")
