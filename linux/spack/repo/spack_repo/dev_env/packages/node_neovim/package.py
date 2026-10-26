import os

from spack_repo.builtin.build_systems.generic import Package

from spack.package import *
from spack_repo.dev_env._npm_vendor import declare_npm_resources, install_npm_application
from spack_repo.dev_env.packages.node_neovim.npm_resources import NPM_PACKAGES


class NodeNeovim(Package):
    """Neovim's Node.js remote-plugin host with a fully pinned npm closure."""

    homepage = "https://github.com/neovim/node-client"
    url = "https://registry.npmjs.org/neovim/-/neovim-5.5.0.tgz"

    license("MIT")

    version("5.5.0", sha512="07af3176be4e5302ee5200fbdda0dadf20a0d742e0ee0aaba080eb49a76f0e9089142e76a4e0f6da2388fa89b3422fac822c53979532387aa701def713946510")
    declare_npm_resources(NPM_PACKAGES, "@=5.5.0")

    depends_on("node-js@20:", type="run")

    def install(self, spec, prefix):
        install_npm_application(
            self.stage.source_path,
            prefix,
            "neovim",
            NPM_PACKAGES,
            {"neovim-node-host": "bin/cli.js"},
            spec["node-js"].prefix.bin.node,
        )
        node = which(spec["node-js"].prefix.bin.node, required=True)
        node("-e", "require(process.argv[1])", prefix.lib.node_modules.neovim)
