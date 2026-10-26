"""Helpers for immutable, network-free npm application packages."""

import os

from spack.package import install, install_tree, mkdirp, resource, symlink


def declare_npm_resources(packages, when):
    for index, (path, name, version, url, checksum) in enumerate(packages):
        validate_npm_path(path)
        resource(
            name="npm-{0:04d}-{1}-{2}".format(index, name.replace("/", "-"), version),
            url=url,
            sha512=checksum,
            placement=".spack-npm/{0:04d}".format(index),
            when=when,
        )


def validate_npm_path(path):
    if not path.startswith("node_modules/") or any(
        part in ("", ".", "..") for part in path.split("/")
    ):
        raise ValueError("npm dependency path must stay inside node_modules: {0}".format(path))


def _resource_source(path):
    if os.path.isfile(os.path.join(path, "package.json")):
        return path
    package = os.path.join(path, "package")
    if os.path.isfile(os.path.join(package, "package.json")):
        return package
    children = [os.path.join(path, item) for item in os.listdir(path)]
    children = [item for item in children if os.path.isdir(item)]
    if len(children) == 1 and os.path.isfile(os.path.join(children[0], "package.json")):
        return children[0]
    raise RuntimeError("cannot locate package.json in npm resource {0}".format(path))


def install_npm_application(source_root, prefix, application, packages, binaries, node):
    for path, _, _, _, _ in packages:
        validate_npm_path(path)
    application_root = prefix.lib.node_modules.join(application)
    mkdirp(application_root)
    for item in os.listdir(source_root):
        if item == ".spack-npm":
            continue
        source = os.path.join(source_root, item)
        destination = application_root.join(item)
        if os.path.isdir(source):
            install_tree(source, destination)
        else:
            install(source, destination)

    for index, (path, _, _, _, _) in enumerate(packages):
        source = _resource_source(os.path.join(source_root, ".spack-npm", "{0:04d}".format(index)))
        install_tree(source, application_root.join(path))

    mkdirp(prefix.bin)
    for command, script in binaries.items():
        target = application_root.join(script)
        link = prefix.bin.join(command)
        symlink(os.path.relpath(target, prefix.bin), link)
        _use_node(target, node)


def _use_node(script, node):
    """Point ``#!/usr/bin/env node`` at the Spack Node; targets have no system node."""
    with open(script, "rb") as stream:
        content = stream.read()
    first, newline, rest = content.partition(b"\n")
    if first.rstrip() != b"#!/usr/bin/env node":
        raise RuntimeError("unexpected npm entry point shebang in {0}: {1!r}".format(script, first))
    with open(script, "wb") as stream:
        stream.write(b"#!" + str(node).encode() + newline + rest)
