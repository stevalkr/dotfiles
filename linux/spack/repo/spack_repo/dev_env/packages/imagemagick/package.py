from spack_repo.builtin.packages.imagemagick.package import Imagemagick as BuiltinImagemagick

from spack.package import *


class Imagemagick(BuiltinImagemagick):
    """Builtin ImageMagick version with the required runtime delegates."""

    depends_on("bzip2")
    depends_on("lcms")
    depends_on("libwebp")
    depends_on("libxml2")
    depends_on("openjpeg")
    depends_on("xz")

    def configure_args(self):
        args = super().configure_args()
        args.extend(
            [
                "--with-bzlib",
                "--with-fontconfig",
                "--with-freetype",
                "--with-heic=no",
                "--with-jpeg",
                "--with-lcms",
                "--with-lzma",
                "--with-openjp2",
                "--with-png",
                "--with-tiff",
                "--with-webp",
                "--with-xml",
            ]
        )
        return args
