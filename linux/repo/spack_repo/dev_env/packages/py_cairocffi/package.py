from spack_repo.builtin.packages.py_cairocffi.package import PyCairocffi as BuiltinPyCairocffi
from spack.package import *


class PyCairocffi(BuiltinPyCairocffi):
    """Load the Spack Cairo library without relying on the target's ldconfig."""

    version("1.7.1", sha256="2e48ee864884ec4a3a34bfa8c9ab9999f688286eb714a15a43ec9d068c36557b")
    depends_on("python@3.8:", type=("build", "run"), when="@1.7:")
    depends_on("py-flit-core@3.2:3", type="build", when="@1.7:")
    depends_on("cairo", type=("link", "run"))

    @run_after("install")
    def select_packaged_cairo(self):
        module = join_path(self.prefix, self.spec["python"].package.site_packages_dir,
                           "cairocffi", "__init__.py")
        # Spack's binary-cache text relocation rewrites this exact store path.
        library = join_path(self.spec["cairo"].prefix.lib, "libcairo.so.2")
        filter_file("ffi, ('cairo-2', 'cairo', 'libcairo-2'),", "ffi, (),", module, string=True)
        filter_file("('libcairo.so.2', 'libcairo.2.dylib', 'libcairo-2.dll')",
                    "({!r},)".format(library), module, string=True)
