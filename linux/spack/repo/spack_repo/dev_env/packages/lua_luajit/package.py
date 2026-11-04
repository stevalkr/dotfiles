from spack_repo.builtin.packages.lua_luajit.package import LuaLuajit as BuiltinLuaLuajit

from spack.package import *


class LuaLuajit(BuiltinLuaLuajit):
    """Upstream LuaJIT at the commit Neovim's own build pins."""

    # The archive's .relver is export-substituted with the commit time, which
    # LuaJIT uses as its release number.
    version(
        "2.1.1788460057",
        url="https://github.com/luajit/luajit/archive/24c20c94e7db195b640854619577441f9b4bc6be.tar.gz",
        sha256="178c656b62bb796e536a23f1d3bb09e1824e4dd28eaf2a4758b295ac328e32e6",
    )
