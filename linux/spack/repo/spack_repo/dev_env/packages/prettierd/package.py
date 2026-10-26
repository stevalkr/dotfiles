from spack_repo.builtin.build_systems.generic import Package
from spack.package import *
from spack_repo.dev_env._npm_vendor import declare_npm_resources, install_npm_application
from spack_repo.dev_env.packages.prettierd.npm_resources import NPM_PACKAGES


class Prettierd(Package):
    """Prettier daemon assembled from pinned npm resources."""

    homepage = "https://github.com/fsouza/prettierd"
    url = "https://registry.npmjs.org/@fsouza/prettierd/-/prettierd-0.29.0.tgz"
    version("0.29.0", sha512="50c04d1405403f655f77c46bb07e1bcdc86dcafa9fcc5a7708e058493626b6bad4e9fc0af8940bcfdb3a83d24d45563a30305691458da4f3badef3c3ffa29316")
    declare_npm_resources(NPM_PACKAGES, "@=0.29.0")
    depends_on("node-js@20:", type="run")

    def install(self, spec, prefix):
        install_npm_application(
            self.stage.source_path, prefix, "prettierd", NPM_PACKAGES,
            {"prettierd": "bin/prettierd"},
            spec["node-js"].prefix.bin.node,
        )
