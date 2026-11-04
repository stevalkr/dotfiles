# shellcheck shell=bash
# Shared by the linux/ commands on the builder and the server (bash 4.4, EL8).

linux_root=$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
out=$linux_root/out
cache=$out/cache
dist=$out/dist
dev_env=$out/dev-env
states=$out/states
bundles=$out/bundle
dev_env_link=$HOME/.local/share/dev-env

# shellcheck source=spack/pins.env
source "$linux_root/spack/pins.env"

id_re='^[0-9]{8}T[0-9]{6}Z-[0-9a-f]{8}$'

# Roots whose commands stay in the view; the nvim wrapper uses them by path.
public_exclude_roots=(python node-js node-neovim)
# Never exposed from public/bin, whatever root provides them.
public_forbidden_re='^(python.*|pip.*|node|npm|npx|corepack)$'

die() {
    printf '%s: %s\n' "${0##*/}" "$*" >&2
    exit 1
}

need() {
    local command
    for command; do
        command -v "$command" >/dev/null 2>&1 || die "$command is required"
    done
}

mirror_state() {
    python3 "$linux_root/scripts/mirror-state.py" "$@"
}

# Builder container --------------------------------------------------------

image=

ensure_image() {
    local hash
    hash=$({
        (cd "$linux_root/container" && find . -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum)
        printf '%s@%s %s\n' "$BUILD_IMAGE" "$BUILD_IMAGE_DIGEST" "$BUILD_PLATFORM"
    } | sha256sum | cut -c1-12)
    image=dev-env:$hash
    docker image inspect "$image" >/dev/null 2>&1 && return
    proxy_env
    local args=() variable
    for variable in "${proxy_variables[@]}"; do
        [[ -n "${!variable:-}" ]] && args+=(--build-arg "$variable")
    done
    [[ -n "${DEV_ENV_DOCKER_NETWORK:-}" ]] && args+=(--network "$DEV_ENV_DOCKER_NETWORK")
    docker build --platform "$BUILD_PLATFORM" "${args[@]}" \
        --build-arg "BASE_IMAGE=$BUILD_IMAGE@$BUILD_IMAGE_DIGEST" \
        --build-arg "IMAGE_HASH=$hash" \
        --file "$linux_root/container/Containerfile" --tag "$image" "$linux_root/container"
}

proxy_variables=(HTTP_PROXY HTTPS_PROXY NO_PROXY http_proxy https_proxy no_proxy)

proxy_env() {
    local pair upper lower
    for pair in HTTP_PROXY:http_proxy HTTPS_PROXY:https_proxy NO_PROXY:no_proxy; do
        upper=${pair%%:*}
        lower=${pair#*:}
        if [[ -n "${!upper:-}" && -z "${!lower:-}" ]]; then
            export "$lower=${!upper}"
        elif [[ -n "${!lower:-}" && -z "${!upper:-}" ]]; then
            export "$upper=${!lower}"
        fi
    done
}

# docker_run [docker run options...] -- command...
# Runs as the host user; callers set HOME to a mount. Spack needs a passwd
# entry for the uid, so minimal passwd/group files are mounted.
docker_run() {
    local uid gid
    uid=$(id -u) gid=$(id -g)
    mkdir -p "$cache/etc"
    printf 'root:x:0:0:root:/root:/bin/bash\ndev-env:x:%s:%s::/tmp:/bin/bash\n' "$uid" "$gid" \
        >"$cache/etc/passwd"
    printf 'root:x:0:\ndev-env:x:%s:\n' "$gid" >"$cache/etc/group"
    local args=(
        --rm --platform "$BUILD_PLATFORM" --user "$uid:$gid"
        # PID 1 ignores Ctrl-C, which docker forwards; tini relays it to the
        # whole process group so the command stops with the client.
        --init --env TINI_KILL_PROCESS_GROUP=1
        --volume "$cache/etc/passwd:/etc/passwd:ro" --volume "$cache/etc/group:/etc/group:ro"
        --security-opt label=disable --security-opt seccomp=unconfined
        --env USER=dev-env
        --env GIT_CONFIG_COUNT=1 --env GIT_CONFIG_KEY_0=safe.directory --env 'GIT_CONFIG_VALUE_0=*'
    )
    local variable
    proxy_env
    for variable in "${proxy_variables[@]}"; do
        [[ -n "${!variable:-}" ]] && args+=(--env "$variable")
    done
    [[ -n "${DEV_ENV_DOCKER_NETWORK:-}" ]] && args+=(--network "$DEV_ENV_DOCKER_NETWORK")
    while (($#)) && [[ "$1" != -- ]]; do
        args+=("$1")
        shift
    done
    shift
    docker run "${args[@]}" "$image" "$@"
}

# Releases -----------------------------------------------------------------

# The store holds absolute paths, so out/dev-env cannot move with the checkout.
dev_env_init() {
    mkdir -p "$dev_env/releases" "$dev_env/mirror" "$dev_env/cache"
    if [[ -f "$dev_env/.root" ]]; then
        [[ "$(<"$dev_env/.root")" == "$dev_env" ]] ||
            die "out/dev-env belongs to $(<"$dev_env/.root"); the checkout must not move"
    else
        printf '%s\n' "$dev_env" >"$dev_env/.root"
    fi
}

# release_id <state-file>
release_id() {
    printf '%s-%s\n' "$(date -u +%Y%m%dT%H%M%SZ)" "$(sha256sum "$1" | cut -c1-8)"
}

newest_release() {
    local id newest=
    for id in "$dev_env"/releases/*; do
        id=${id##*/}
        [[ "$id" =~ $id_re ]] && newest=$id
    done
    printf '%s\n' "$newest"
}

# use_release_spack <release-dir>: offline Spack with the release's target config.
use_release_spack() {
    local release=$1
    export SPACK_PYTHON=${SPACK_PYTHON:-$(command -v python3)}
    export SPACK_ROOT=$release/spack
    export SPACK_USER_CONFIG_PATH=$release/target
    export SPACK_SYSTEM_CONFIG_PATH=$release/target/system
    export SPACK_USER_CACHE_PATH=$dev_env/cache/user
    export PATH=$SPACK_ROOT/bin:/usr/bin:/bin
    export PIP_NO_INDEX=1 npm_config_offline=true CARGO_NET_OFFLINE=true GIT_TERMINAL_PROMPT=0
    unset SPACK_ENV ALL_PROXY all_proxy "${proxy_variables[@]}"
}
