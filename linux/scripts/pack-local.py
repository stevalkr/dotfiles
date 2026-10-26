#!/usr/bin/env python3
"""Pack prepared Neovim data (~/.local/share/nvim) for other homes. Python 3.6.

Symlinks inside the tree become relative, links out of it are replaced by
copies, and the prepare home in rplugin.vim becomes expand('$HOME'). Fails if
the prepare home or the checkout path remains in any file.
"""
import argparse
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile

TREE = ".local/share/nvim"
# Top-level entries that are per-machine state, not prepared data.
SKIP = {"swap", "shada", "undo", "sessions", "log", "logs"}
CHECKOUT = "/opt/dotfiles"


def die(message):
    sys.exit("pack-local: " + message)


def copy_tree(source, destination):
    """Copy source to destination, keeping in-tree links as relative links."""
    root = os.path.realpath(source)
    os.makedirs(destination)
    for directory, dirs, files in os.walk(source):
        relative = os.path.relpath(directory, source)
        if relative == ".":
            dirs[:] = [d for d in dirs if d not in SKIP]
            files = [f for f in files if f not in SKIP]
        target_dir = os.path.normpath(os.path.join(destination, relative))
        for name in sorted(dirs + files):
            path = os.path.join(directory, name)
            output = os.path.join(target_dir, name)
            if os.path.islink(path):
                resolved = os.path.realpath(path)
                if not os.path.exists(resolved):
                    die("dangling link: " + path)
                if resolved == root or resolved.startswith(root + os.sep):
                    inside = os.path.join(destination, os.path.relpath(resolved, root))
                    os.symlink(os.path.relpath(inside, target_dir), output)
                elif os.path.isdir(resolved):
                    shutil.copytree(resolved, output, symlinks=False)
                else:
                    shutil.copy2(resolved, output)
                if name in dirs:
                    dirs.remove(name)  # not walked: linked or copied whole
            elif os.path.isdir(path):
                os.mkdir(output)
            elif os.path.isfile(path):
                shutil.copy2(path, output)
            else:
                die("unsupported file type: " + path)


def normalize_rplugin(path, home):
    if not os.path.isfile(path):
        return
    with open(path) as stream:
        text = stream.read()
    text = text.replace("'" + home + "/.local/", "expand('$HOME') . '/.local/")
    with open(path, "w") as stream:
        stream.write(text)


def find_paths(tree, needles):
    found = []
    for directory, _, files in os.walk(tree):
        for name in files:
            path = os.path.join(directory, name)
            if os.path.islink(path):
                continue
            with open(path, "rb") as stream:
                content = stream.read()
            if any(needle in content for needle in needles):
                found.append(os.path.relpath(path, tree))
    return sorted(found)


def reset(info):
    info.uid = info.gid = 0
    info.uname = info.gname = ""
    info.mtime = 0
    return info


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("home")
    parser.add_argument("output")
    args = parser.parse_args()
    home = os.path.realpath(args.home)
    source = os.path.join(home, TREE)
    if not os.path.isdir(source) or os.path.islink(source):
        die("missing or linked " + source)

    staging = tempfile.mkdtemp(dir=os.path.dirname(os.path.abspath(args.output)))
    try:
        tree = os.path.join(staging, TREE)
        copy_tree(source, tree)
        normalize_rplugin(os.path.join(tree, "rplugin.vim"), home)
        found = find_paths(tree, (home.encode(), CHECKOUT.encode()))
        if found:
            die("prepare paths remain in:\n  " + "\n  ".join(found))

        archive = os.path.join(staging, "local.tar")
        paths = [os.path.join(staging, ".local"), os.path.join(staging, ".local/share")]
        for directory, dirs, files in os.walk(tree):
            paths.append(directory)
            paths += [os.path.join(directory, name) for name in files]
            paths += [os.path.join(directory, name) for name in dirs
                      if os.path.islink(os.path.join(directory, name))]
        # Sorted paths list parents first; fixed metadata keeps the archive stable.
        with tarfile.open(archive, "w", format=tarfile.GNU_FORMAT) as output:
            for path in sorted(paths):
                output.add(path, arcname=os.path.relpath(path, staging), recursive=False,
                           filter=reset)
        subprocess.check_call(["zstd", "-q", "-19", "-T4", "-f", archive, "-o", args.output + ".tmp"])
        os.rename(args.output + ".tmp", args.output)
    finally:
        shutil.rmtree(staging)
    print("pack-local: " + args.output)


if __name__ == "__main__":
    main()
