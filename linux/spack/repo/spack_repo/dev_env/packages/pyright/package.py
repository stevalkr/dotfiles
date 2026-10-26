from spack_repo.builtin.build_systems.generic import Package

from spack.package import *
from spack_repo.dev_env._npm_vendor import install_npm_application


class Pyright(Package):
    """Pyright Node application; the Linux runtime has no npm dependencies."""

    homepage = "https://github.com/microsoft/pyright"
    url = "https://registry.npmjs.org/pyright/-/pyright-1.1.414.tgz"

    license("MIT")

    version("1.1.414", sha512="14f6596f9d637a90d7e1e3fb4c460378d16d984dd683092411c269bc7dff426512b23d04032dcb5eefb10784ff1560de8edb179427c5affadb5858f0bb0b97c3")

    depends_on("node-js@20:", type="run")

    def install(self, spec, prefix):
        install_npm_application(
            self.stage.source_path,
            prefix,
            "pyright",
            (),
            {"pyright": "index.js", "pyright-langserver": "langserver.index.js"},
            spec["node-js"].prefix.bin.node,
        )
