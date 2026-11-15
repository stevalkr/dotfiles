import os
import shutil

from spack_repo.builtin.packages.llvm.package import Llvm as BuiltinLlvm

from spack.package import *


_RUNTIMES = "@=22.1.5 +clang libcxx=runtime libunwind=runtime platform=linux target=x86_64"


class Llvm(BuiltinLlvm):
    """Builtin LLVM with portable runtime paths, no build-host GCC config and
    only the user-facing tools: no libexec/llvm build-tree copy, static
    libraries, CMake packages or LLVM development and offload tools."""

    depends_on("patchelf", type="build", when=_RUNTIMES)

    @run_after("install", when=_RUNTIMES)
    def repair_runtime_rpaths(self):
        patchelf = Executable(self.spec["patchelf"].prefix.bin.patchelf)
        stage_root = os.path.dirname(self.stage.path) + "/"
        files = (
            (join_path(self.prefix, "lib/x86_64-unknown-linux-gnu/libc++.so.1.0"), True),
            (join_path(self.prefix, "lib/x86_64-unknown-linux-gnu/libc++abi.so.1.0"), True),
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


# Commands kept in bin; everything else there is an LLVM development, test or
# offload tool. Links are kept with their targets. This also drops builtin
# post_install's build-host ``--gcc-install-dir`` configs (clang.cfg): targets
# have no Spack GCC, and without them clang finds the system GCC itself.
_BIN_KEEP = {
    # clang driver and C/C++ tooling
    "clang", "clang++", "clang-22", "clang-cpp", "clang-cl",
    "clangd", "clang-format", "git-clang-format",
    "clang-tidy", "run-clang-tidy", "clang-apply-replacements",
    "clang-include-cleaner", "clang-query", "clang-check", "clang-scan-deps",
    "scan-build", "scan-build-py", "scan-view", "analyze-build", "intercept-build",
    # linkers
    "lld", "ld.lld", "ld64.lld", "lld-link", "wasm-ld",
    # binutils replacements, sanitizer symbolizer, coverage
    "llvm-ar", "llvm-ranlib", "llvm-lib", "llvm-nm", "llvm-objcopy", "llvm-strip",
    "llvm-objdump", "llvm-readobj", "llvm-readelf", "llvm-size", "llvm-strings",
    "llvm-symbolizer", "llvm-addr2line", "llvm-cxxfilt", "llvm-dwarfdump",
    "llvm-profdata", "llvm-cov", "llvm-config",
    # IR and machine-code tools
    "opt", "llc", "lli", "llvm-as", "llvm-dis", "llvm-link", "llvm-mc", "llvm-mca",
}


def _prune(prefix):
    """Remove what a toolchain install does not need."""
    shutil.rmtree(join_path(prefix, "libexec", "llvm"))
    for name in os.listdir(prefix.bin):
        if name not in _BIN_KEEP:
            os.remove(join_path(prefix.bin, name))
    for name in _BIN_KEEP:
        if not os.path.exists(join_path(prefix.bin, name)):
            raise InstallError("LLVM prune: missing bin/" + name)
    # Runtime archives (libc++.a, libunwind.a) live in the target subdirectory.
    for name in os.listdir(prefix.lib):
        if name.endswith(".a"):
            os.remove(join_path(prefix.lib, name))
    # The exported CMake targets name the removed archives and tools.
    for name in ("llvm", "clang", "lld"):
        shutil.rmtree(join_path(prefix.lib, "cmake", name))


def _toolchain_only(post_install):
    """Run builtin post_install, then prune the install."""

    def wrapper(pkg):
        post_install(pkg)
        _prune(pkg.prefix)

    return wrapper


# Callbacks are stored as function objects, so overriding post_install by name
# would not replace the inherited one.
_callbacks = Llvm._run_after_callbacks
Llvm._run_after_callbacks = [
    (key, _toolchain_only(fn) if fn is BuiltinLlvm.post_install else fn)
    for key, fn in _callbacks
]
if Llvm._run_after_callbacks == _callbacks:
    raise RuntimeError("builtin LLVM post_install callback not found")
del _callbacks
