from spack_repo.builtin.packages.py_pynvim.package import PyPynvim as BuiltinPyPynvim

from spack.package import *


class PyPynvim(BuiltinPyPynvim):
    version("0.6.0", sha256="0ffcb879322d08f9e9061e1123dd58ba3a5ccfbd4999bb1157bac525822aa590")

    with when("@0.6:"):
        depends_on("py-msgpack@1:", type=("build", "run"))
        depends_on("py-greenlet@3:", type=("build", "run"))
        depends_on("py-typing-extensions@4.5:", type=("build", "run"), when="^python@:3.11")
