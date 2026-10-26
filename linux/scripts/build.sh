#!/usr/bin/env bash
# In the build container: build the environment, push its runtime closure to
# the release mirror and write the release files.
set -euo pipefail

scripts=/opt/dev-env/scripts
env_dir=/opt/dev-env-env
packages=/opt/dev-env-dist/packages
mirror=$packages/mirror

export SPACK_ROOT=/opt/spack SPACK_PYTHON=/usr/bin/python3
export SPACK_USER_CONFIG_PATH=/opt/dev-env/spack/config
export SPACK_SYSTEM_CONFIG_PATH=/opt/dev-env-system-config
export PATH=$SPACK_ROOT/bin:$PATH

die() {
    printf 'build: %s\n' "$*" >&2
    exit 1
}

source /etc/os-release
[[ "$ID $VERSION_ID" == 'rocky 8.7' ]] || die "expected Rocky Linux 8.7, found $ID $VERSION_ID"
[[ "$(getconf GNU_LIBC_VERSION)" == 'glibc 2.28' ]] || die "expected glibc 2.28"
[[ "$(uname -m)" == x86_64 ]] || die "expected x86_64"
[[ "$(gcc -dumpfullversion)" == 8.5.0 ]] || die "expected GCC 8.5.0"

spack --version
spack clean --misc-cache
# Node is built with GCC 13; Spack needs it installed before solving.
spack install --fail-fast --show-log-on-error 'gcc@=13.4.0 languages=c,c++ ~bootstrap %gcc@8.5.0'

cp /opt/dev-env/spack/spack.yaml "$env_dir/spack.yaml"
# Installed compilers (llvm) are reused even when excluded, so a build of an
# older dev_env recipe can return. Uninstall such builds and concretize again.
stale=$(mktemp)
cat >"$stale.py" <<'EOF_PY'
import spack.environment
for spec in spack.environment.active_environment().all_specs():
    if spec.namespace == "dev_env" and not spec.external:
        if spec._package_hash != spec.package.content_hash():
            print(spec.dag_hash())
EOF_PY
for attempt in 1 2; do
    spack -e "$env_dir" concretize --force
    spack -e "$env_dir" python "$stale.py" >"$stale"
    [[ -s "$stale" ]] || break
    ((attempt == 1)) || die "still built from older dev_env recipes: $(tr '\n' ' ' <"$stale")"
    sed 's|^|/|' "$stale" | xargs spack uninstall -y --force
done
rm -f -- "$stale" "$stale.py"
spack -e "$env_dir" install --fail-fast --show-log-on-error

# The mirror holds exactly the runtime (link+run) closure of the lock.
spack -e "$env_dir" buildcache push --unsigned --private --without-build-dependencies dev-env
keep=$(mktemp)
python3 "$scripts/mirror-state.py" closure "$env_dir/spack.lock" >"$keep"
spack buildcache prune --keeplist "$keep" dev-env
rm -f "$keep"
spack buildcache update-index dev-env
# Fails if the mirror and the closure differ.
python3 "$scripts/mirror-state.py" state --mirror "$mirror" --lock "$env_dir/spack.lock" >/dev/null

# Release files are reproducible, so unchanged ones drop out of incremental bundles.
pack() { # pack <output> <tar arguments...>
    local output=$1
    shift
    tar --sort=name --mtime=@0 --owner=0 --group=0 --numeric-owner --format=gnu \
        --mode=u+rwX,go+rX,go-w \
        --exclude=.git --exclude=__pycache__ --exclude='*.pyc' \
        -cf - "$@" | zstd -q -19 -T4 -o "$output.tmp" -f
    mv "$output.tmp" "$output"
}
pack "$packages/spack.tar.zst" -C /opt spack spack-packages
pack "$packages/env.tar.zst" -C "$env_dir" spack.yaml spack.lock -C /opt/dev-env/spack repo target

printf 'build: %s\n' "$(spack -e "$env_dir" find --no-groups | wc -l) installed specs"
