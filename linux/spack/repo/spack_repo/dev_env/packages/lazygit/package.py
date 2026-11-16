from spack_repo.builtin.packages.lazygit.package import Lazygit as BuiltinLazygit
from spack_repo.dev_env._dependencies import restrict_dependency_type

from spack.package import *


class Lazygit(BuiltinLazygit):
    """Builtin lazygit; it runs the host's git, kept out of the view."""

    version("0.66.3", sha256="49e80d28e03e53048105f6ebb5afefbe5caacffa8549347d8a59eab3a00dafe1")

    depends_on("go@1.26:", type="build", when="@0.66:")


restrict_dependency_type(Lazygit, "git", ())
