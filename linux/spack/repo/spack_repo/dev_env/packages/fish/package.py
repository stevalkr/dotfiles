from spack_repo.builtin.packages.fish.package import Fish as BuiltinFish

from spack.package import *
from spack_repo.dev_env._dependencies import restrict_dependency_type


class Fish(BuiltinFish):
    """Builtin fish; Rust is only its compiler, its standard library is linked in."""

    version("4.9.3", sha256="20998a25f73217ddcc19f499055fd587e9912d1ad6e7109120fbcf2871f0b98c")

    def cmake_args(self):
        # fish 4.3 renamed BUILD_DOCS and rejects the old option.
        if self.spec.satisfies("@4.3:"):
            return [self.define_from_variant("WITH_DOCS", "docs")]
        return super().cmake_args()


restrict_dependency_type(Fish, "rust", "build")
