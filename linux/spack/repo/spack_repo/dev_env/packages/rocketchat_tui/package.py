from spack_repo.builtin.build_systems.go import GoPackage

from spack.package import *
from spack_repo.dev_env._go_vendor import configure_go_vendor, declare_go_module_resources
from spack_repo.dev_env.packages.rocketchat_tui.go_resources import GO_MODULES, MODULES_TXT


class RocketchatTui(GoPackage):
    homepage = "https://github.com/RocketChat/rocketchat-tui"
    git = "https://github.com/RocketChat/rocketchat-tui.git"

    license("MIT")

    version("2022.11.21", commit="f57c57e7a09c833cf0e25af9e47d90292dc98201")

    # Let Go's standard help handling exit before loading chat configuration.
    patch("help-before-config.patch", when="@=2022.11.21")

    depends_on("go@1.19:", type="build")

    declare_go_module_resources(GO_MODULES, "@=2022.11.21")

    @run_before("build", when="@=2022.11.21")
    def configure_offline_go(self):
        configure_go_vendor(self.stage.source_path, GO_MODULES, MODULES_TXT)

    def setup_build_environment(self, env):
        super().setup_build_environment(env)
        env.set("GOPROXY", "off")
        env.set("GOSUMDB", "off")
        env.set("GOFLAGS", "-mod=vendor")
