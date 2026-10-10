#!/usr/bin/env python3
"""Refresh selected regular-file records in a Spack install manifest."""

import base64
import hashlib
import json
import os
import stat
import sys
from pathlib import Path


def entry(path):
    metadata = path.lstat()
    if not stat.S_ISREG(metadata.st_mode):
        raise ValueError("manifest refresh only supports regular files: {0}".format(path))
    digest = hashlib.sha1()
    with path.open("rb") as stream:
        while True:
            block = stream.read(1024 * 1024)
            if not block:
                break
            digest.update(block)
    return {
        "mode": metadata.st_mode,
        "owner": metadata.st_uid,
        "group": metadata.st_gid,
        "hash": base64.b32encode(digest.digest()).decode(),
        "time": metadata.st_mtime,
        "size": metadata.st_size,
    }


def main():
    if len(sys.argv) == 2 and sys.argv[1] in ("-h", "--help", "help"):
        print("Usage: _refresh-install-manifest.py <prefix> <file>...")
        return 0
    if len(sys.argv) < 3:
        print("usage: _refresh-install-manifest.py <prefix> <file>...", file=sys.stderr)
        return 2
    prefix = Path(sys.argv[1]).resolve()
    manifest_path = prefix / ".spack" / "install_manifest.json"
    if not manifest_path.is_file():
        raise ValueError("Spack install manifest is missing: {0}".format(manifest_path))
    with manifest_path.open(encoding="utf-8") as stream:
        manifest = json.load(stream)
    for value in sys.argv[2:]:
        path = Path(value).resolve()
        if os.path.commonpath([str(prefix), str(path)]) != str(prefix):
            raise ValueError("file is outside package prefix: {0}".format(path))
        key = str(path)
        if key not in manifest:
            raise ValueError("file is absent from Spack install manifest: {0}".format(path))
        manifest[key] = entry(path)
    temporary = manifest_path.with_name(manifest_path.name + ".tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(manifest, stream, separators=(",", ":"))
    os.chmod(str(temporary), manifest_path.stat().st_mode)
    os.replace(str(temporary), str(manifest_path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
