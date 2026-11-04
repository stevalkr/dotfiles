from spack_repo.builtin.packages.fish.package import Fish as BuiltinFish

from spack.package import *
from spack_repo.dev_env._dependencies import restrict_dependency_type


class Fish(BuiltinFish):
    """Builtin fish; Rust is only its compiler, its standard library is linked in."""


restrict_dependency_type(Fish, "rust", "build")
