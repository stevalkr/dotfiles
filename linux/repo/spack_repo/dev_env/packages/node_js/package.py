import gzip
import hashlib
import os

from spack_repo.builtin.build_systems.generic import Package

from spack.package import *


class NodeJs(Package):
    """Official EL8-compatible Node.js runtime, without the bundled npm tree."""

    homepage = "https://nodejs.org/"
    url = "https://nodejs.org/dist/v26.7.0/node-v26.7.0-linux-x64.tar.xz"

    license("Unicode-TOU")

    version("26.7.0", sha256="982aa24dd8be4c889c6a8ab337ddff3b0896645b20f4239356e80552c16277ee")

    variant("doc", default=False, description="Install Node documentation")
    variant("openssl", default=True, description="Require the bundled OpenSSL runtime")
    variant("zlib", default=True, description="Require the bundled zlib runtime")

    conflicts("~openssl", msg="The official Node runtime includes OpenSSL")
    conflicts("~zlib", msg="The official Node runtime includes zlib")

    # Keep the compatibility library in Node's prefix so the launcher can
    # provide it without rewriting the unusual V8 ELF executable.
    depends_on("node-libatomic@=8.5.0-16.el8_7", type="build")

    def install(self, spec, prefix):
        mkdirp(prefix.bin, prefix.lib, prefix.libexec.node)
        install_tree("include/node", prefix.include.node)
        libatomic = self.spec["node-libatomic"].prefix.lib
        install(join_path(libatomic, "libatomic.so.1.2.0"), prefix.lib)

        mkdirp(prefix.share.doc.node)
        for name in ("LICENSE", "README.md"):
            install(name, prefix.share.doc.node)
        if "+doc" in spec:
            install("CHANGELOG.md", prefix.share.doc.node)
            mkdirp(prefix.share.man.man1)
            install("share/man/man1/node.1", prefix.share.man.man1)

        # Spack registers every ELF in a buildcache for relocation. Its parser
        # falls back to patchelf for this unusual V8 executable even when the
        # executable needs no change, moving the first LOAD segment away from
        # offset zero and making Node abort. Store the pristine payload in a
        # non-ELF form and materialize it atomically in the user's cache.
        payload = join_path(prefix.libexec.node, "node.gz")
        with open("bin/node", "rb") as source, open(payload, "wb") as output:
            with gzip.GzipFile(filename="", mode="wb", fileobj=output, mtime=0) as compressed:
                compressed.write(source.read())
        with open(payload, "rb") as stream:
            payload_sha256 = hashlib.sha256(stream.read()).hexdigest()

        launcher = """#!/usr/bin/env bash
set -euo pipefail

self=$(readlink -f -- "${BASH_SOURCE[0]}")
prefix=$(CDPATH= cd -- "$(dirname -- "$self")/.." && pwd)
payload="$prefix/libexec/node/node.gz"
runtime_parent="${XDG_CACHE_HOME:-${HOME:?}/.cache}/dev-env"
runtime_root="$runtime_parent/node-26.7.0-%s"
runtime="$runtime_root/node"

if [[ ! -x "$runtime" ]]; then
    mkdir -p "$runtime_parent"
    staging=$(mktemp -d "$runtime_parent/.node-26.7.0.XXXXXXXX")
    trap 'rm -rf -- "$staging"' EXIT
    mkdir -p "$staging/lib"
    /usr/bin/python3 -c 'import gzip, shutil, sys; shutil.copyfileobj(gzip.open(sys.argv[1], "rb"), open(sys.argv[2], "wb"))' "$payload" "$staging/node"
    chmod 0755 "$staging/node"
    cp "$prefix/lib/libatomic.so.1.2.0" "$staging/lib/"
    ln -s libatomic.so.1.2.0 "$staging/lib/libatomic.so.1"
    if ! mv -T "$staging" "$runtime_root" 2>/dev/null; then
        rm -rf -- "$staging"
    fi
    trap - EXIT
fi

export LD_LIBRARY_PATH="$runtime_root/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
exec "$runtime" "$@"
""" % payload_sha256
        with open(prefix.bin.node, "w", encoding="utf-8") as stream:
            stream.write(launcher)
        os.chmod(prefix.bin.node, 0o755)
        which(prefix.bin.node, required=True)("--version")
