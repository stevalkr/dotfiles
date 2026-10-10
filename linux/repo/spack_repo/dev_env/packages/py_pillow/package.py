from spack_repo.builtin.packages.py_pillow.package import PyPillow as BuiltinPyPillow

from spack.package import *


class PyPillow(BuiltinPyPillow):
    """Builtin Pillow with the complete WebP link interface."""

    # Pillow 11+ folded the old webpmux feature into its single WebP feature.
    # The pinned builtin recipe still applies this constraint only to the
    # webpmux variant, which no longer exists for these Pillow versions.
    depends_on("libwebp+libwebpmux+libwebpdemux", when="@11:+webp")
