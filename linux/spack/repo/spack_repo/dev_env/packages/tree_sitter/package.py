from spack_repo.builtin.packages.tree_sitter.package import TreeSitter as BuiltinTreeSitter

from spack.package import *
from spack_repo.dev_env._cargo_vendor import configure_crates_io_vendor, declare_crate_resources
from spack_repo.dev_env._dependencies import restrict_dependency_type
from spack_repo.dev_env.packages.tree_sitter.cargo_resources import CRATES


class TreeSitter(BuiltinTreeSitter):
    git = "https://github.com/tree-sitter/tree-sitter.git"

    version("0.27.0-dev.20260821", commit="baad4174e551e527bde1b069f4b41082e4abd085")
    declare_crate_resources(resource, CRATES, "@=0.27.0-dev.20260821")

    depends_on("rust@1.84:", type="build", when="@=0.27.0-dev.20260821+cli")

    @run_before("build", when="@=0.27.0-dev.20260821+cli")
    def configure_offline_cargo(self):
        configure_crates_io_vendor(self.stage.source_path, CRATES)


# The CLI compiles grammars with the target's own C compiler; shipping the
# Spack GCC that builds Node would add it and binutils to every release.
restrict_dependency_type(TreeSitter, "c", "build")
