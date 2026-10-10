#!/usr/bin/env bash
set -euo pipefail

script_dir="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

usage() {
    cat <<'EOF'
Usage:
  ./scripts/_patch-elf.sh inspect <elf-file>
  ./scripts/_patch-elf.sh set-rpath <elf-file> <rpath>
  ./scripts/_patch-elf.sh repair-llvm-22.1.5 <llvm-prefix>

Inspect one ELF file or apply one demonstrated RPATH repair. The command never
sets LD_LIBRARY_PATH and never scans or modifies a directory recursively.
EOF
}

case "${1:-}" in
    -h|--help|help|"")
        usage
        exit 0
        ;;
    inspect)
        (($# == 2)) || { usage >&2; exit 2; }
        file=$2
        test -f "$file" || { printf 'patch-elf: not a file: %s\n' "$file" >&2; exit 2; }
        readelf -hW "$file" >/dev/null
        readelf -lW "$file" | grep -E 'Requesting program interpreter' || true
        readelf -dW "$file" | grep -E '\((NEEDED|RPATH|RUNPATH)\)' || true
        ;;
    set-rpath)
        (($# == 3)) || { usage >&2; exit 2; }
        file=$2
        rpath=$3
        test -f "$file" || { printf 'patch-elf: not a file: %s\n' "$file" >&2; exit 2; }
        [[ "$rpath" != *'/usr/local/'* && "$rpath" != *'/opt/dev-env-build-stage/'* ]] || {
            printf '%s\n' 'patch-elf: refusing a host/build RPATH' >&2
            exit 2
        }
        command -v patchelf >/dev/null 2>&1 || {
            printf '%s\n' 'patch-elf: patchelf is required' >&2
            exit 2
        }
        readelf -hW "$file" >/dev/null
        printf 'Before:\n'
        patchelf --print-rpath "$file"
        # --no-sort is required for compatibility with the bundled Node binary
        # and is harmless for explicit repairs to other files.
        patchelf --no-sort --set-rpath "$rpath" "$file"
        printf 'After:\n'
        patchelf --print-rpath "$file"
        ;;
    repair-llvm-22.1.5)
        (($# == 2)) || { usage >&2; exit 2; }
        prefix=${2%/}
        [[ -d "$prefix/lib/x86_64-unknown-linux-gnu" ]] || {
            printf 'patch-elf: not an LLVM 22.1.5 prefix: %s\n' "$prefix" >&2
            exit 2
        }
        command -v patchelf >/dev/null 2>&1 || {
            printf '%s\n' 'patch-elf: patchelf is required' >&2
            exit 2
        }
        repaired_files=()
        for relative in \
            lib/x86_64-unknown-linux-gnu/libc++.so.1.0 \
            lib/x86_64-unknown-linux-gnu/libc++abi.so.1.0 \
            libexec/llvm/c-index-test; do
            file="$prefix/$relative"
            test -f "$file" || { printf 'patch-elf: missing expected file: %s\n' "$file" >&2; exit 1; }
            old_rpath=$(patchelf --print-rpath "$file")
            new_rpath=
            IFS=: read -r -a entries <<<"$old_rpath"
            if [[ "$relative" == lib/x86_64-unknown-linux-gnu/* ]]; then
                new_rpath='$ORIGIN'
            fi
            for entry in "${entries[@]}"; do
                [[ "$entry" == /opt/dev-env-build-stage/* ]] && continue
                case ":$new_rpath:" in
                    *":$entry:"*) ;;
                    *) new_rpath="${new_rpath:+$new_rpath:}$entry" ;;
                esac
            done
            [[ -n "$new_rpath" ]] || { printf 'patch-elf: empty repaired RPATH: %s\n' "$file" >&2; exit 1; }
            patchelf --no-sort --set-rpath "$new_rpath" "$file"
            [[ "$(patchelf --print-rpath "$file")" != *'/opt/dev-env-build-stage/'* ]]
            repaired_files+=("$file")
            printf 'Repaired: %s\n' "$file"
        done
        python3 "$script_dir/_refresh-install-manifest.py" "$prefix" "${repaired_files[@]}"
        printf '%s\n' 'Refreshed: Spack install manifest records for repaired files'
        ;;
    *)
        usage >&2
        exit 2
        ;;
esac
