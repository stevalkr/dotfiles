from spack_repo.builtin.build_systems.python import PythonPackage
from spack.package import *


class PyCmakelang(PythonPackage):
    """CMake formatter and linter."""

    homepage = "https://github.com/cheshirekow/cmake_format"
    pypi = "cmakelang/cmakelang-0.6.13.tar.gz"
    version("0.6.13", sha256="03982e87b00654d024d73ef972d9d9bb0e5726cdb6b8a424a15661fb6278e67f")
    depends_on("py-setuptools", type="build")
    depends_on("py-six", type=("build", "run"))
