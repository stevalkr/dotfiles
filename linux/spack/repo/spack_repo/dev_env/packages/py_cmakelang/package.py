from spack_repo.builtin.build_systems.python import PythonPackage
from spack.package import *


class PyCmakelang(PythonPackage):
    """CMake formatter and linter."""

    homepage = "https://github.com/cheshirekow/cmake_format"
    pypi = "cmakelang/cmakelang-0.6.13.tar.gz"
    version("0.6.13", sha256="03982e87b00654d024d73ef972d9d9bb0e5726cdb6b8a424a15661fb6278e67f")
    depends_on("py-setuptools", type="build")
    depends_on("py-six", type=("build", "run"))

    def patch(self):
        # The sdist puts its README at the root.
        filter_file("cmakelang/doc/README.rst", "README.rst", "setup.py", string=True)
        # Build cmakelang without the subsequent legacy metapackage setup calls.
        with open("setup.py", encoding="utf-8") as source:
            setup = source.read()
        setup = setup[: setup.index('\nsetup(\n    name="cmake-annotate",')]
        with open("setup.py", "w", encoding="utf-8") as source:
            source.write(setup)
