from spack_repo.builtin.build_systems.generic import Package

from spack.package import *


class ClaudeCode(Package):
    """Claude Code native Linux build: a Bun executable with an appended payload."""

    homepage = "https://claude.com/claude-code"
    url = "https://downloads.claude.ai/claude-code-releases/2.1.308/linux-x64/claude"

    license("UNKNOWN")

    # sha256: platforms["linux-x64"].checksum in <version>/manifest.json
    version(
        "2.1.308",
        sha256="356733f185fa988e6bf3aa9a555269fdd167982a2e2a80d3c8a78037bb92ad58",
        expand=False,
    )

    # Spack would parse the version from "x64".
    def url_for_version(self, version):
        return f"https://downloads.claude.ai/claude-code-releases/{version}/linux-x64/claude"

    def install(self, spec, prefix):
        mkdirp(prefix.bin)
        install(self.stage.archive_file, prefix.bin.claude)
        set_executable(prefix.bin.claude)
