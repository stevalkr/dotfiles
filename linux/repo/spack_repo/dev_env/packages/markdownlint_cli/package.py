from spack_repo.builtin.build_systems.generic import Package

from spack.package import *
from spack_repo.dev_env._npm_vendor import declare_npm_resources, install_npm_application
from spack_repo.dev_env.packages.markdownlint_cli.npm_resources import NPM_PACKAGES


class MarkdownlintCli(Package):
    """markdownlint-cli assembled from immutable npm tarballs without npm install."""

    homepage = "https://github.com/igorshubovych/markdownlint-cli"
    url = "https://registry.npmjs.org/markdownlint-cli/-/markdownlint-cli-0.49.1.tgz"

    license("MIT")

    version("0.49.1", sha256="3a98ad54490c1589bb5fd3ecc863eb2d76e7b25191b3a0b98b885f2d97431b8c")
    declare_npm_resources(NPM_PACKAGES, "@=0.49.1")

    depends_on("node-js@26.7.0", type="run")

    def install(self, spec, prefix):
        install_npm_application(
            self.stage.source_path,
            prefix,
            "markdownlint-cli",
            NPM_PACKAGES,
            {"markdownlint": "markdownlint.js"},
        )
        node = which(spec["node-js"].prefix.bin.node, required=True)
        node(prefix.lib.node_modules.join("markdownlint-cli/markdownlint.js"), "--version")
