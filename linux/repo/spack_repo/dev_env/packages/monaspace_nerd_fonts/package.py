from spack_repo.builtin.build_systems.generic import Package

from spack.package import *


class MonaspaceNerdFonts(Package):
    """Monaspace Nerd Font desktop faces, installed without touching system fonts."""

    homepage = "https://monaspace.githubnext.com/"
    url = "https://github.com/githubnext/monaspace/releases/download/v1.400/monaspace-nerdfonts-v1.400.zip"

    license("OFL-1.1")

    version("1.400", sha256="9b7f9505d977601d8819dfdb57fa4b49bdab61132b6d1131c2e8d092066edc5a")

    def install(self, spec, prefix):
        destination = prefix.share.fonts.monaspace
        mkdirp(destination)
        fonts = find(".", "*.otf", recursive=True) + find(".", "*.ttf", recursive=True)
        if not fonts:
            raise InstallError("Monaspace Nerd Font archive contains no desktop fonts")
        for font in fonts:
            install(font, destination)
