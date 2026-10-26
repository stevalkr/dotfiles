#!/usr/bin/env python3
"""Mirror closure and release state. Runs on the server too: Python 3.6.

A state is a sorted ``sha256  path`` list: ``mirror/<path>`` for the v3 layout
file, spec manifests and the blobs they reference (the index is excluded, it is
regenerated), and bare names for release files.
"""
import argparse
import errno
import hashlib
import json
import os
import sys

SPEC_DIR = "v3/manifests/spec"
LAYOUT = "v3/layout.json"
MANIFEST_SUFFIX = ".spec.manifest.json"


def die(message):
    sys.exit("mirror-state: " + message)


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_state(path):
    state = {}
    with open(path) as stream:
        for line in stream:
            digest, sep, name = line.rstrip("\n").partition("  ")
            if not sep or len(digest) != 64 or not name or name in state:
                die("bad state line in {}: {!r}".format(path, line))
            if name.startswith("/") or any(p in ("", ".", "..") for p in name.split("/")):
                die("bad state path in {}: {}".format(path, name))
            state[name] = digest
    return state


def write_state(state, stream=sys.stdout):
    for name in sorted(state):
        stream.write("{}  {}\n".format(state[name], name))


def closure(lock_path):
    """DAG hashes of the roots' link and run closure, without externals."""
    with open(lock_path) as stream:
        lock = json.load(stream)
    specs = lock["concrete_specs"]
    seen = set()
    todo = [root["hash"] for root in lock["roots"]]
    while todo:
        dag_hash = todo.pop()
        if dag_hash in seen:
            continue
        spec = specs[dag_hash]
        if "external" in spec:
            continue
        seen.add(dag_hash)
        for dependency in spec.get("dependencies", ()):
            if {"link", "run"} & set(dependency["parameters"]["deptypes"]):
                todo.append(dependency["hash"])
    return seen


def manifests(mirror):
    """{dag hash: mirror-relative manifest path}"""
    result = {}
    root = os.path.join(mirror, SPEC_DIR)
    for directory, _, files in os.walk(root):
        for name in files:
            if not name.endswith(MANIFEST_SUFFIX):
                die("unexpected file in spec manifests: " + os.path.join(directory, name))
            dag_hash = name[: -len(MANIFEST_SUFFIX)].rsplit("-", 1)[-1]
            result[dag_hash] = os.path.relpath(os.path.join(directory, name), mirror)
    return result


def mirror_state(mirror, lock_path=None):
    found = manifests(mirror)
    if lock_path:
        wanted = closure(lock_path)
        missing = sorted(wanted - set(found))
        extra = sorted(set(found) - wanted)
        if missing or extra:
            die("mirror differs from the lock closure; missing {}, extra {}".format(missing, extra))
    state = {"mirror/" + LAYOUT: sha256(os.path.join(mirror, LAYOUT))}
    for path in found.values():
        full = os.path.join(mirror, path)
        state["mirror/" + path] = sha256(full)
        with open(full) as stream:
            records = json.load(stream)["data"]
        for record in records:
            if record["checksumAlgorithm"] != "sha256":
                die("unsupported blob checksum in " + path)
            checksum = record["checksum"]
            blob = "blobs/sha256/{}/{}".format(checksum[:2], checksum)
            if not os.path.isfile(os.path.join(mirror, blob)):
                die("missing blob {} for {}".format(blob, path))
            # Blobs are content addressed; their name is their checksum.
            state["mirror/" + blob] = checksum
    return state


def parse_files(pairs):
    files = {}
    for pair in pairs:
        name, sep, path = pair.partition("=")
        if not sep or "/" in name:
            die("expected NAME=PATH, got " + pair)
        files[name] = path
    return files


def source_of(name, mirror, files):
    if name.startswith("mirror/"):
        if not mirror:
            die("no mirror given for " + name)
        return os.path.join(mirror, name[len("mirror/"):])
    if name not in files:
        die("no source for " + name)
    return files[name]


def place(source, destination):
    """Hard-link, or copy, source to destination atomically."""
    os.makedirs(os.path.dirname(destination), exist_ok=True)
    temporary = destination + ".tmp"
    if os.path.lexists(temporary):
        os.remove(temporary)
    try:
        os.link(source, temporary)
    except OSError as error:
        if error.errno not in (errno.EXDEV, errno.EPERM, errno.EMLINK):
            raise
        with open(source, "rb") as src, open(temporary, "wb") as dst:
            for chunk in iter(lambda: src.read(1 << 20), b""):
                dst.write(chunk)
    os.rename(temporary, destination)


def cmd_closure(args):
    for dag_hash in sorted(closure(args.lock)):
        print(dag_hash)


def cmd_state(args):
    state = mirror_state(args.mirror, args.lock)
    for name, path in parse_files(args.files).items():
        state[name] = sha256(path)
    write_state(state)


def cmd_diff(args):
    base = read_state(args.base)
    for name, digest in sorted(read_state(args.new).items()):
        if base.get(name) != digest:
            print(name)


def cmd_stage(args):
    """Link the listed state entries into DEST under their state paths."""
    files = parse_files(args.files)
    with open(args.list) as stream:
        for name in stream.read().splitlines():
            place(source_of(name, args.mirror, files), os.path.join(args.dest, name))


def cmd_check(args):
    """Verify incoming objects; everything else must already be on hand."""
    state = read_state(args.state)
    for directory, _, names in os.walk(args.objects):
        for name in names:
            path = os.path.relpath(os.path.join(directory, name), args.objects)
            if path not in state:
                die("object not in state: " + path)
    for name, digest in sorted(state.items()):
        incoming = os.path.join(args.objects, name)
        if os.path.isfile(incoming):
            if sha256(incoming) != digest:
                die("checksum mismatch: " + name)
        elif name.startswith("mirror/"):
            if not os.path.isfile(source_of(name, args.mirror, {})):
                die("missing from archive and mirror: " + name)
        elif not args.base or sha256(os.path.join(args.base, name)) != digest:
            die("missing from archive and base release: " + name)


def cmd_files(args):
    """Verify the state's release files in DIR."""
    for name, digest in sorted(read_state(args.state).items()):
        if not name.startswith("mirror/") and sha256(os.path.join(args.dir, name)) != digest:
            die("checksum mismatch: " + name)


def cmd_ingest(args):
    """Add the state's mirror entries from SRC to DST; existing blobs are kept."""
    for name, digest in sorted(read_state(args.state).items()):
        if not name.startswith("mirror/"):
            continue
        destination = source_of(name, args.dst, {})
        if os.path.isfile(destination) and (
            name.startswith("mirror/blobs/") or sha256(destination) == digest
        ):
            continue
        source = source_of(name, args.src, {})
        if not os.path.isfile(source):
            die("missing source object: " + source)
        place(source, destination)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command")

    sub = commands.add_parser("closure", help="hashes of the runtime closure")
    sub.add_argument("lock")
    sub.set_defaults(func=cmd_closure)

    sub = commands.add_parser("state", help="print a state")
    sub.add_argument("--mirror", required=True)
    sub.add_argument("--lock", help="require the mirror to be exactly this closure")
    sub.add_argument("files", nargs="*", metavar="NAME=PATH")
    sub.set_defaults(func=cmd_state)

    sub = commands.add_parser("diff", help="entries of NEW not in BASE")
    sub.add_argument("base")
    sub.add_argument("new")
    sub.set_defaults(func=cmd_diff)

    sub = commands.add_parser("stage", help="link listed entries into DEST")
    sub.add_argument("--mirror")
    sub.add_argument("list")
    sub.add_argument("dest")
    sub.add_argument("files", nargs="*", metavar="NAME=PATH")
    sub.set_defaults(func=cmd_stage)

    sub = commands.add_parser("check", help="verify an unpacked bundle")
    sub.add_argument("--mirror", required=True)
    sub.add_argument("--base")
    sub.add_argument("state")
    sub.add_argument("objects")
    sub.set_defaults(func=cmd_check)

    sub = commands.add_parser("files", help="verify release files in DIR")
    sub.add_argument("state")
    sub.add_argument("dir")
    sub.set_defaults(func=cmd_files)

    sub = commands.add_parser("ingest", help="add mirror entries of a state")
    sub.add_argument("state")
    sub.add_argument("src")
    sub.add_argument("dst")
    sub.set_defaults(func=cmd_ingest)

    args = parser.parse_args()
    if not args.command:
        parser.error("a command is required")
    args.func(args)


if __name__ == "__main__":
    main()
