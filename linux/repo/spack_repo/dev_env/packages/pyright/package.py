from spack_repo.builtin.build_systems.generic import Package
from spack_repo.dev_env._lsp_test import test_language_server

from spack.package import *
from spack_repo.dev_env._npm_vendor import install_npm_application


class Pyright(Package):
    """Pyright Node application; the Linux runtime has no npm dependencies."""

    homepage = "https://github.com/microsoft/pyright"
    url = "https://registry.npmjs.org/pyright/-/pyright-1.1.413.tgz"

    license("MIT")

    version("1.1.413", sha256="7322a75188e788f9fe7cbb71891af435a713bf8985141dc0d28e8ca243977bee")

    depends_on("node-js@26.7.0", type="run")

    def install(self, spec, prefix):
        install_npm_application(
            self.stage.source_path,
            prefix,
            "pyright",
            (),
            {"pyright": "index.js", "pyright-langserver": "langserver.index.js"},
        )
