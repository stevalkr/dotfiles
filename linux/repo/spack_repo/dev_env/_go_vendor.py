"""Helpers shared by project recipes that build Go modules offline."""

import os
import shutil

from spack.package import mkdirp, resource


def _copytree_merge(source, destination):
    """Copy a tree into an existing directory using Python 3.6 APIs."""
    mkdirp(destination)
    for name in os.listdir(source):
        source_path = os.path.join(source, name)
        destination_path = os.path.join(destination, name)
        if os.path.isdir(source_path):
            _copytree_merge(source_path, destination_path)
        else:
            shutil.copy2(source_path, destination_path)


def _declared_module(go_mod):
    try:
        with open(go_mod) as source:
            for line in source:
                fields = line.strip().split()
                if len(fields) == 2 and fields[0] == "module":
                    return fields[1]
    except (IOError, OSError):
        pass
    return None


def _contains_packages(candidate, module, packages):
    for package in packages:
        relative = os.path.relpath(package, module)
        if relative == ".":
            if not any(name.endswith(".go") for name in os.listdir(candidate)):
                return False
        elif not os.path.isdir(os.path.join(candidate, relative)):
            return False
    return True


def _module_root(extracted, module, packages):
    """Find a module root whether Spack flattened its Go proxy ZIP or not."""
    candidates = []
    for root, directories, files in os.walk(extracted):
        directories.sort()
        if (
            "go.mod" in files
            and _declared_module(os.path.join(root, "go.mod")) == module
            and _contains_packages(root, module, packages)
        ):
            return root
        if _contains_packages(root, module, packages):
            candidates.append(root)

    if candidates:
        return min(candidates, key=lambda path: (path.count(os.sep), path))
    raise RuntimeError(
        "cannot locate module {0} packages beneath staged resource {1}".format(module, extracted)
    )


def declare_go_module_resources(modules, when):
    """Declare the exact module zip graph as checksummed Spack resources."""
    for index, (_, _, checksum, url, _) in enumerate(modules):
        resource(
            name="go-module-{0:03d}".format(index),
            url=url,
            sha256=checksum,
            placement=".spack-go-modules/{0:03d}".format(index),
            when=when,
        )


def configure_go_vendor(source_root, modules, modules_txt):
    """Recreate Go's vendor tree from already-staged module resources."""
    resource_root = os.path.join(source_root, ".spack-go-modules")
    vendor_root = os.path.join(source_root, "vendor")
    mkdirp(vendor_root)

    for index, (module, _, _, _, packages) in enumerate(modules):
        extracted = os.path.join(resource_root, "{0:03d}".format(index))
        module_root = _module_root(extracted, module, packages)
        for package in packages:
            relative = os.path.relpath(package, module)
            source = module_root if relative == "." else os.path.join(module_root, relative)
            destination = os.path.join(vendor_root, package)
            mkdirp(os.path.dirname(destination))
            _copytree_merge(source, destination)

    with open(os.path.join(vendor_root, "modules.txt"), "w") as destination:
        destination.write(modules_txt)
