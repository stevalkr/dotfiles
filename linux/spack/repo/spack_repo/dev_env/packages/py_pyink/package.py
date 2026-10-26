from spack_repo.builtin.build_systems.python import PythonPackage

from spack.package import *


class PyPyink(PythonPackage):
    """Pyink formatter, paired with its exact Black library dependency."""

    homepage = "https://github.com/google/pyink"
    pypi = "pyink/pyink-26.5.1.tar.gz"

    license("MIT")

    version("26.5.1", sha256="d74d3aa19102069a679160be50cc1340e2fa9d04eece25c24c583e0d85404302")

    depends_on("python@3.10:", type=("build", "run"))
    depends_on("py-hatchling@1.27:", type="build")
    depends_on("py-hatch-vcs", type="build")
    depends_on("py-black@=26.5.1+jupyter~d~colorama~uvloop", type=("build", "run"))
    depends_on("py-click@8:", type=("build", "run"))
    depends_on("py-mypy-extensions@0.4.3:", type=("build", "run"))
    depends_on("py-packaging@22:", type=("build", "run"))
    depends_on("py-pathspec@1:", type=("build", "run"))
    depends_on("py-platformdirs@2:", type=("build", "run"))
    depends_on("py-pytokens@0.4.0:0.4.999", type=("build", "run"))
