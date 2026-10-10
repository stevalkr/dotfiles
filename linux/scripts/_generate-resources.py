#!/usr/bin/env python3
import argparse
import base64
import hashlib
import json
import re
import zipfile
from pathlib import Path


CARGO_FIELD = re.compile(r'^(name|version|source|checksum) = "(.*)"$', re.MULTILINE)
GO_MODULE = re.compile(r"^# (\S+) (v\S+)$")


def write_cargo(args):
    packages = []
    lock_text = args.lockfile.read_text()
    for block in lock_text.split("[[package]]")[1:]:
        fields = dict(CARGO_FIELD.findall(block))
        if fields.get("source", "").startswith("registry+"):
            packages.append((fields["name"], fields["version"], fields["checksum"]))

    lines = [
        '"""Generated from {0}; do not edit by hand."""'.format(args.lockfile.name),
        "",
        "CRATES = (",
    ]
    lines.extend("    {!r},".format(package) for package in sorted(set(packages)))
    lines.extend((")", ""))
    write_output(args.output, lines)


def write_npm(args):
    lock = json.loads(args.lockfile.read_text())
    packages = []
    for path, metadata in sorted(lock["packages"].items()):
        if not path or "resolved" not in metadata:
            continue
        if not path.startswith("node_modules/") or any(
            part in ("", ".", "..") for part in path.split("/")
        ):
            raise ValueError("npm lock path must be inside node_modules: {0}".format(path))
        algorithm, encoded = metadata["integrity"].split("-", 1)
        if algorithm != "sha512":
            raise ValueError("expected sha512 npm integrity for {0}".format(path))
        packages.append(
            (
                path,
                metadata.get("name", path.rsplit("node_modules/", 1)[-1]),
                metadata["version"],
                metadata["resolved"],
                base64.b64decode(encoded).hex(),
            )
        )

    lines = [
        '"""Generated from {0}; do not edit by hand."""'.format(args.lockfile.name),
        "",
        "NPM_PACKAGES = (",
    ]
    lines.extend("    {!r},".format(package) for package in packages)
    lines.extend((")", ""))
    write_output(args.output, lines)


def module_packages(modules_txt):
    modules = []
    current = None
    for line in modules_txt.read_text().splitlines():
        match = GO_MODULE.match(line)
        if match:
            current = [match.group(1), match.group(2), []]
            modules.append(current)
        elif current is not None and line and not line.startswith("#"):
            current[2].append(line)
    return modules


def cached_zips(cache):
    result = {}
    for archive in cache.glob("**/*.zip"):
        with zipfile.ZipFile(archive) as source:
            first = source.namelist()[0]
        prefix = first[: first.find("/", first.find("@"))]
        path, version = prefix.rsplit("@", 1)
        result[(path, version)] = archive
    return result


def write_go(args):
    archives = cached_zips(args.module_cache)
    records = []
    for path, version, packages in module_packages(args.modules_txt):
        archive = archives[(path, version)]
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        escaped = archive.relative_to(args.module_cache).as_posix()[:-4]
        url = "https://proxy.golang.org/{0}.zip".format(escaped)
        records.append((path, version, digest, url, tuple(packages)))

    lines = ['"""Generated from vendor/modules.txt; do not edit by hand."""', "", "GO_MODULES = ("]
    lines.extend("    {0!r},".format(record) for record in records)
    lines.extend((")", "", "MODULES_TXT = " + repr(args.modules_txt.read_text()), ""))
    write_output(args.output, lines)


def write_output(path, lines):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="kind", required=True)

    cargo = subparsers.add_parser("cargo")
    cargo.add_argument("lockfile", type=Path)
    cargo.add_argument("output", type=Path)
    cargo.set_defaults(handler=write_cargo)

    npm = subparsers.add_parser("npm")
    npm.add_argument("lockfile", type=Path)
    npm.add_argument("output", type=Path)
    npm.set_defaults(handler=write_npm)

    go = subparsers.add_parser("go")
    go.add_argument("modules_txt", type=Path)
    go.add_argument("module_cache", type=Path)
    go.add_argument("output", type=Path)
    go.set_defaults(handler=write_go)

    args = parser.parse_args()
    args.handler(args)


if __name__ == "__main__":
    main()
