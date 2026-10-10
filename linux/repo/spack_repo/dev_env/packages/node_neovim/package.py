import os

from spack_repo.builtin.build_systems.generic import Package

from spack.package import *
from spack_repo.dev_env._npm_vendor import declare_npm_resources, install_npm_application
from spack_repo.dev_env.packages.node_neovim.npm_resources import NPM_PACKAGES


class NodeNeovim(Package):
    """Neovim's Node.js remote-plugin host with a fully pinned npm closure."""

    homepage = "https://github.com/neovim/node-client"
    url = "https://registry.npmjs.org/neovim/-/neovim-5.4.0.tgz"

    license("MIT")

    version("5.4.0", sha256="0f28cc0f83a9ab714627398fca7164614348c3aa53cdf57f1e79fbfeda3418a8")
    declare_npm_resources(NPM_PACKAGES, "@=5.4.0")

    depends_on("node-js@26.7.0", type="run")

    def install(self, spec, prefix):
        install_npm_application(
            self.stage.source_path,
            prefix,
            "neovim",
            NPM_PACKAGES,
            {"neovim-node-host": "bin/cli.js"},
        )
        node = which(spec["node-js"].prefix.bin.node, required=True)
        node("-e", "require(process.argv[1])", prefix.lib.node_modules.neovim)
