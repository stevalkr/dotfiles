import tarfile

from spack_repo.builtin.build_systems.generic import Package

from spack.package import *


class NodeLibatomic(Package):
    """Rocky 8.7 libatomic runtime required by the official Node binary."""

    homepage = "https://download.rockylinux.org/vault/rocky/8.7/"
    url = "https://dl.rockylinux.org/vault/rocky/8.7/BaseOS/x86_64/os/Packages/l/libatomic-8.5.0-16.el8_7.x86_64.rpm"

    license("GPL-3.0-or-later WITH GCC-exception-3.1")

    version(
        "8.5.0-16.el8_7",
        sha256="5de43e8039814083a1646492368e53fc262cec8f6a2026fced371b8e79d5f258",
        expand=False,
    )

    depends_on("rpm", type="build")

    def install(self, spec, prefix):
        rpm2archive = which(self.spec["rpm"].prefix.bin.rpm2archive, required=True)
        local_rpm = join_path(self.stage.path, "libatomic.rpm")
        install(self.stage.archive_file, local_rpm)
        converted = local_rpm + ".tgz"
        rpm2archive(local_rpm, output=converted)

        extracted = join_path(self.stage.path, "libatomic-root")
        mkdirp(extracted)
        with tarfile.open(converted, "r:gz") as archive:
            archive.extractall(extracted)
        install_tree(join_path(extracted, "usr", "lib64"), prefix.lib)
