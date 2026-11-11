from spack_repo.builtin.packages.py_zope_interface.package import (
    PyZopeInterface as BuiltinPyZopeInterface,
)

from spack.package import *
from spack_repo.dev_env._dependencies import restrict_dependency_when


class PyZopeInterface(BuiltinPyZopeInterface):
    """Release that builds with current setuptools and imports on Python 3.14."""

    version("8.7", sha256="0b47b62e8d0d99b24bcdd32f4f2120425e5019c3bee2ad69a0e1d75737487a96")

    # Interface classes get __classdictcell__ on 3.14, which 7.0 rejects.
    conflicts("^python@3.14:", when="@:7.1")

    def url_for_version(self, version):
        url = "https://files.pythonhosted.org/packages/source/z/zope.interface/{}-{}.tar.gz"
        name = "zope_interface" if version >= Version("8") else "zope.interface"
        return url.format(name, version)


# Only 7.x caps setuptools; 8 uses PEP 420 namespaces instead of pkg_resources.
restrict_dependency_when(PyZopeInterface, "py-setuptools@:73", "@7.1:7")
