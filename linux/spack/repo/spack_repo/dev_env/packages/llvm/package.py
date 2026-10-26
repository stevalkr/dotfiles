import os

from spack_repo.builtin.packages.llvm.package import Llvm as BuiltinLlvm

from spack.package import *


_RUNTIMES = "@=22.1.5 +clang libcxx=runtime libunwind=runtime platform=linux target=x86_64"


class Llvm(BuiltinLlvm):
    """Builtin LLVM with portable runtime paths and no build-host GCC config."""

    depends_on("patchelf", type="build", when=_RUNTIMES)

    # Derived package callbacks precede inherited ones. Repair the build-tree
    # c-index-test before builtin post_install copies it into libexec/llvm.
    # Spack records checksums after all install callbacks have completed.
    @run_after("install", when=_RUNTIMES)
    def repair_runtime_rpaths(self):
        patchelf = Executable(self.spec["patchelf"].prefix.bin.patchelf)
        stage_root = os.path.dirname(self.stage.path) + "/"
        files = (
            (join_path(self.prefix, "lib/x86_64-unknown-linux-gnu/libc++.so.1.0"), True),
            (join_path(self.prefix, "lib/x86_64-unknown-linux-gnu/libc++abi.so.1.0"), True),
            (join_path(self.build_directory, "bin/c-index-test"), False),
        )
        for path, add_origin in files:
            if not os.path.isfile(path):
                raise InstallError("LLVM runtime-path repair: missing " + path)
            old = patchelf("--print-rpath", path, output=str).strip()
            entries = ["$ORIGIN"] if add_origin else []
            for entry in old.split(":"):
                if not entry or entry.startswith(stage_root):
                    continue
                if entry not in entries:
                    entries.append(entry)
            if not entries:
                raise InstallError("LLVM runtime-path repair: empty RPATH for " + path)
            new = ":".join(entries)
            if new != old:
                patchelf("--no-sort", "--set-rpath", new, path)


def _without_gcc_install_dir(post_install):
    """Run builtin post_install, then drop its build-host ``--gcc-install-dir`` configs.

    Targets have no Spack GCC; without the configs clang finds the system GCC itself.
    """

    def wrapper(pkg):
        post_install(pkg)
        for cfg in ("clang.cfg", "clang++.cfg"):
            path = join_path(pkg.prefix.bin, cfg)
            if os.path.lexists(path):
                os.remove(path)

    return wrapper


# Callbacks are stored as function objects, so overriding post_install by name
# would not replace the inherited one.
_callbacks = Llvm._run_after_callbacks
Llvm._run_after_callbacks = [
    (key, _without_gcc_install_dir(fn) if fn is BuiltinLlvm.post_install else fn)
    for key, fn in _callbacks
]
if Llvm._run_after_callbacks == _callbacks:
    raise RuntimeError("builtin LLVM post_install callback not found")
del _callbacks
