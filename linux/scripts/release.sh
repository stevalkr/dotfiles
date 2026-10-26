#!/usr/bin/env bash
# release.sh <id> <state> <files-dir> [<base-release-dir>]
# Create out/dev-env/releases/<id> from release files in <files-dir>, taking the
# ones it lacks from the base release. Mirror objects must already be ingested.
set -euo pipefail
# shellcheck source=../lib.sh
source "$(dirname -- "${BASH_SOURCE[0]}")/../lib.sh"

(($# == 3 || $# == 4)) || die 'usage: release.sh <id> <state> <files-dir> [<base-release-dir>]'
id=$1 state=$2 files=$3 base=${4:-}
[[ "$id" =~ $id_re ]] || die "bad release id: $id"
release=$dev_env/releases/$id
[[ ! -e "$release" ]] || die "release exists: $id"

temporary=$dev_env/releases/.tmp-$id
rm -rf -- "$temporary"
mkdir -p "$temporary"
trap 'rm -rf -- "$temporary"' EXIT

names=()
while read -r _ name; do
    [[ "$name" == mirror/* ]] || names+=("$name")
done <"$state"
for name in spack.tar.zst env.tar.zst; do
    [[ " ${names[*]} " == *" $name "* ]] || die "state has no $name"
done
sources=()
for name in "${names[@]}"; do
    if [[ -f "$files/$name" ]]; then
        sources+=("$name=$files/$name")
    elif [[ -n "$base" && -f "$base/$name" ]]; then
        sources+=("$name=$base/$name")
    else
        die "missing release file: $name"
    fi
done
mirror_state stage <(printf '%s\n' "${names[@]}") "$temporary" "${sources[@]}"
mirror_state files "$state" "$temporary"
cp -- "$state" "$temporary/state.sha256"

for name in spack.tar.zst env.tar.zst; do
    tar -I zstd --no-same-owner -xf "$temporary/$name" -C "$temporary"
done
[[ -x "$temporary/spack/bin/spack" && -f "$temporary/spack.lock" ]] || die 'incomplete release files'

(
    use_release_spack "$temporary"
    spack buildcache update-index dev-env
)
mv -- "$temporary" "$release"
trap - EXIT
printf 'release: %s\n' "$id"
