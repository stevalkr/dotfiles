#!/usr/bin/env bash
set -euo pipefail

# shellcheck source=_common.sh
source "$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/_common.sh"

usage() {
    printf '%s\n' 'Usage: internal builder preparation'
}

case "${1:-}" in
    -h|--help|help)
        usage
        exit 0
        ;;
    "") ;;
    *)
        usage >&2
        exit 2
        ;;
esac

require_command docker
require_command git
require_command sha256sum

mkdir -p "$source_cache"

clone_pinned() {
    local name=$1 url=$2 tag=$3 commit=$4
    local destination="$source_cache/$name"
    local actual_commit origin

    if [[ ! -d "$destination/.git" ]]; then
        if [[ -e "$destination" ]]; then
            printf 'dev-env: %s exists but is not a Git checkout\n' "$destination" >&2
            exit 1
        fi
        git clone --depth 1 --branch "$tag" "$url" "$destination"
    fi

    actual_commit="$(git -C "$destination" rev-parse HEAD)"
    [[ -z "$(git -C "$destination" status --porcelain)" ]] || {
        printf 'dev-env: modified pinned source cache: %s\n' "$destination" >&2
        exit 1
    }
    if [[ "$actual_commit" != "$commit" ]]; then
        origin="$(git -C "$destination" remote get-url origin)"
        [[ "$origin" == "$url" ]] || {
            printf 'dev-env: %s has unexpected origin %s\n' "$destination" "$origin" >&2
            exit 1
        }
        git -C "$destination" fetch --depth 1 origin "$commit"
        git -C "$destination" checkout --detach "$commit"
        actual_commit="$(git -C "$destination" rev-parse HEAD)"
    fi
    [[ "$actual_commit" == "$commit" ]] || {
        printf 'dev-env: %s is at %s; expected %s\n' \
            "$destination" "$actual_commit" "$commit" >&2
        exit 1
    }
    printf '%s: %s\n' "$name" "$actual_commit"
}

clone_pinned spack "$SPACK_GIT_URL" "$SPACK_TAG" "$SPACK_COMMIT"
clone_pinned spack-packages \
    "$SPACK_PACKAGES_GIT_URL" \
    "$SPACK_PACKAGES_TAG" \
    "$SPACK_PACKAGES_COMMIT"

builder_definition_sha256="$({
    cd "$project_root"
    find Containerfile.build container config repo -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum
    sha256sum spack.yaml
} | sha256sum | awk '{print $1}')"

image_label() {
    docker image inspect \
        --format "{{ index .Config.Labels \"$1\" }}" \
        "$builder_image" 2>/dev/null
}

if [[ "$(image_label dev-env.spack-commit || true)" == "$SPACK_COMMIT" && \
      "$(image_label dev-env.spack-packages-commit || true)" == "$SPACK_PACKAGES_COMMIT" && \
      "$(image_label dev-env.build-image-digest || true)" == "$BUILD_IMAGE_DIGEST" && \
      "$(image_label dev-env.build-platform || true)" == "$BUILD_PLATFORM" && \
      "$(image_label dev-env.builder-definition-sha256 || true)" == "$builder_definition_sha256" ]]; then
    printf 'dev-env: builder image already prepared: %s\n' "$builder_image"
    exit 0
fi

prepare_proxy_environment
prepare_docker_network

exec docker build \
    --platform "$BUILD_PLATFORM" \
    "${docker_network_build_args[@]}" \
    "${docker_proxy_build_args[@]}" \
    --build-arg "BUILD_IMAGE_REF=$BUILD_IMAGE@$BUILD_IMAGE_DIGEST" \
    --build-arg "SPACK_COMMIT=$SPACK_COMMIT" \
    --build-arg "SPACK_PACKAGES_COMMIT=$SPACK_PACKAGES_COMMIT" \
    --build-arg "BUILD_IMAGE_DIGEST=$BUILD_IMAGE_DIGEST" \
    --build-arg "BUILD_PLATFORM=$BUILD_PLATFORM" \
    --build-arg "BUILDER_DEFINITION_SHA256=$builder_definition_sha256" \
    --file "$project_root/Containerfile.build" \
    --tag "$builder_image" \
    "$project_root"
