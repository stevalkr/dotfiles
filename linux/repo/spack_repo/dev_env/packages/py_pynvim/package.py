from spack_repo.builtin.packages.py_pynvim.package import PyPynvim as BuiltinPyPynvim

from spack.package import *


class PyPynvim(BuiltinPyPynvim):
    """Builtin pynvim with importlib-based plugin loading for Python 3.13."""

    patch("python313.patch", when="@0.4.3 ^python@3.12:")
    # The first synchronous call initializes the plugin and must preserve
    # its return value just like subsequent requests.
    patch("first-request.patch", when="@0.4.3")
