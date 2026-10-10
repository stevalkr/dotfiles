#!/usr/bin/env python3
"""Archive only prepared Linux runtime data and normalize rplugin registration."""
import argparse
import json
import posixpath
import re
import shutil
import tarfile
import tempfile
from pathlib import Path

TREES = ('.local/share/nvim',)
SKIP = {'swap', 'shada', 'undo', 'sessions', 'log', 'logs'}


def normalize_rplugin(path, prepared_home):
    if not path.is_file():
        return
    text = path.read_text()
    lines = []
    for line in text.splitlines(True):
        if 'remote#host#RegisterPlugin(' in line:
            line = line.replace("'" + prepared_home.rstrip('/') + '/.local/',
                                "expand('$HOME') . '/.local/")
            if re.search(r"remote#host#RegisterPlugin\([^,]+,\s*'/", line):
                raise ValueError('unrecognized absolute rplugin registration')
        lines.append(line)
    path.write_text(''.join(lines))


def pack(home, archive):
    marker = home / '.local/share/dotfiles-linux/prepared.json'
    identity = json.loads(marker.read_text())
    if identity['platform'] != 'Linux' or identity['architecture'] != 'x86_64':
        raise ValueError('runtime data must be prepared on Linux x86-64')
    for private in ('python', 'node'):
        if (home / '.local/share/nvim' / private).exists():
            raise ValueError('provider environments belong to packages, not local data: ' + private)
    with tempfile.TemporaryDirectory() as directory:
        staging = Path(directory)
        for tree in TREES:
            source = home / tree
            if not source.is_dir() or source.is_symlink():
                raise ValueError('prepared runtime tree is missing or is a link: ' + tree)
            shutil.copytree(str(source), str(staging / tree), symlinks=True,
                            ignore=lambda _path, names: set(names) & SKIP)
        normalize_rplugin(staging / '.local/share/nvim/rplugin.vim', identity['home'])
        with tarfile.open(str(archive), 'w') as output:
            for tree in TREES:
                output.add(str(staging / tree), arcname=tree)


def install(home, archive):
    with tarfile.open(str(archive), 'r') as source:
        members = source.getmembers()
        links = {m.name.rstrip("/") for m in members if m.issym() or m.islnk()}
        replace_links = []
        for member in members:
            name = member.name.rstrip('/')
            if not any(name == tree or name.startswith(tree + '/') for tree in TREES):
                raise ValueError('unexpected runtime archive path: ' + name)
            for parent in Path(name).parents:
                if parent.as_posix() in links:
                    raise ValueError('archive path traverses a link: ' + name)
            if posixpath.normpath(name) != name:
                raise ValueError('non-normalized runtime archive path: ' + name)
            if member.issym() or member.islnk():
                target = member.linkname
                if member.issym():
                    target = posixpath.normpath(posixpath.join(posixpath.dirname(name), target))
                if not any(target == tree or target.startswith(tree + '/') for tree in TREES):
                    raise ValueError('runtime link escapes prepared trees: ' + name)
            elif not (member.isdir() or member.isfile()):
                raise ValueError('unsupported runtime archive entry: ' + name)
            # Refuse extraction through links already present in the target.
            destination = home / name
            for parent in (destination,) + tuple(destination.parents):
                if parent == home.parent:
                    break
                if parent == destination and parent.is_symlink() and not member.isdir():
                    replace_links.append(parent)
                    continue
                if parent.is_symlink():
                    raise ValueError('runtime destination is a symlink: ' + str(parent))
        for path in set(replace_links):
            path.unlink()
        home.mkdir(parents=True, exist_ok=True)
        # Link targets above have been constrained to the data tree.
        source.extractall(str(home), members=members)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('pack', 'install'))
    parser.add_argument('home', type=Path)
    parser.add_argument('archive', type=Path)
    args = parser.parse_args()
    globals()[args.operation](args.home.resolve(), args.archive)


if __name__ == '__main__':
    main()
