"""Helpers shared by project recipes that build Cargo packages offline."""

import hashlib
import json
import os

from spack.package import mkdirp


def crate_download_url(name, version):
    """Return a crates.io URL whose fragment exposes the archive type to Spack."""
    endpoint = "https://static.crates.io/crates/{0}/{0}-{1}.crate".format(name, version)
    return "{0}#{1}-{2}.tar.gz".format(endpoint, name, version)


def declare_crate_resources(resource, crates, when):
    """Declare every crates.io archive in a lockfile as a Spack resource."""
    for name, version, checksum in crates:
        resource(
            name="crate-{0}-{1}".format(name.replace("_", "-"), version),
            # Spack 1.2.2 does not recognize .crate, but it uses the full URL
            # (including an untransmitted fragment) to infer the archive type.
            url=crate_download_url(name, version),
            sha256=checksum,
            extension="tar.gz",
            placement=".spack-vendor/{0}-{1}".format(name, version),
            when=when,
        )


def _files_checksum(directory):
    files = {}
    for root, dirs, names in os.walk(directory):
        dirs.sort()
        for name in sorted(names):
            path = os.path.join(root, name)
            relative = os.path.relpath(path, directory)
            if relative == ".cargo-checksum.json":
                continue
            with open(path, "rb") as source:
                files[relative] = hashlib.sha256(source.read()).hexdigest()
    return files


def configure_crates_io_vendor(source_root, crates):
    """Turn extracted crate resources into a Cargo vendor directory."""
    vendor_root = os.path.join(source_root, ".spack-vendor")
    for name, version, checksum in crates:
        directory = os.path.join(vendor_root, "{0}-{1}".format(name, version))
        # Resource expansion can preserve the archive's one top-level folder.
        if not os.path.isfile(os.path.join(directory, "Cargo.toml")):
            children = [os.path.join(directory, item) for item in os.listdir(directory)]
            children = [item for item in children if os.path.isdir(item)]
            if len(children) == 1 and os.path.isfile(os.path.join(children[0], "Cargo.toml")):
                nested = children[0]
                for item in os.listdir(nested):
                    os.rename(os.path.join(nested, item), os.path.join(directory, item))
                os.rmdir(nested)
        metadata = {"files": _files_checksum(directory), "package": checksum}
        with open(os.path.join(directory, ".cargo-checksum.json"), "w") as destination:
            json.dump(metadata, destination, sort_keys=True, separators=(",", ":"))

    cargo_dir = os.path.join(source_root, ".cargo")
    mkdirp(cargo_dir)
    with open(os.path.join(cargo_dir, "config.toml"), "w") as config:
        config.write(
            '[source.crates-io]\nreplace-with = "spack-vendor"\n\n'
            '[source.spack-vendor]\ndirectory = "{0}"\n\n'
            "[net]\noffline = true\n".format(vendor_root.replace("\\", "\\\\"))
        )
