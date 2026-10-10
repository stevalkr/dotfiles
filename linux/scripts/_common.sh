#!/usr/bin/env bash

script_dir="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
project_root="$(CDPATH= cd -- "$script_dir/.." && pwd)"

# shellcheck source=../config/spack-pins.env
source "$project_root/config/spack-pins.env"

work_root="$project_root/out"
source_cache="$work_root/sources"
spack_environment="$work_root/spack"
build_root="$work_root/build"
cache_root="$work_root/cache"
environment_root="$work_root/environment"
log_root="$work_root/logs"
manifest_root="$work_root/manifests"
mirror_root="$work_root/packages/mirror"
offline_bootstrap_root="$work_root/bootstrap"
bundle_root="$work_root/packages"
builder_image="dev-env-build:${SPACK_COMMIT:0:12}"
proxy_variables=(HTTP_PROXY HTTPS_PROXY NO_PROXY http_proxy https_proxy no_proxy)

require_command() {
    command -v "$1" >/dev/null 2>&1 || {
        printf 'dev-env: %s is required\n' "$1" >&2
        exit 2
    }
}

prepare_output_tree() {
    mkdir -p \
        "$spack_environment" \
        "$build_root/home" \
        "$build_root/stage" \
        "$build_root/store" \
        "$cache_root/bootstrap" \
        "$cache_root/misc" \
        "$cache_root/sources" \
        "$environment_root" \
        "$log_root" \
        "$manifest_root" \
        "$mirror_root" \
        "$offline_bootstrap_root" \
        "$bundle_root"
}

prepare_proxy_environment() {
    local pair uppercase lowercase variable value

    for pair in HTTP_PROXY:http_proxy HTTPS_PROXY:https_proxy NO_PROXY:no_proxy; do
        uppercase="${pair%%:*}"
        lowercase="${pair#*:}"
        if [[ -n "${!uppercase-}" && -z "${!lowercase-}" ]]; then
            printf -v "$lowercase" '%s' "${!uppercase}"
            export "$lowercase"
        elif [[ -n "${!lowercase-}" && -z "${!uppercase-}" ]]; then
            printf -v "$uppercase" '%s' "${!lowercase}"
            export "$uppercase"
        fi
    done

    docker_proxy_build_args=()
    docker_proxy_run_args=()

    for variable in "${proxy_variables[@]}"; do
        value="${!variable-}"
        if [[ -n "$value" ]]; then
            export "$variable"
            docker_proxy_build_args+=(--build-arg "$variable")
            docker_proxy_run_args+=(--env "$variable")
        fi
    done
}

prepare_docker_network() {
    local network="${DEV_ENV_DOCKER_NETWORK:-}"

    docker_network_build_args=()
    docker_network_run_args=()
    if [[ -z "$network" ]]; then
        return
    fi
    if [[ ! "$network" =~ ^[A-Za-z0-9_.:-]+$ ]]; then
        printf 'dev-env: invalid DEV_ENV_DOCKER_NETWORK: %s\n' "$network" >&2
        return 2
    fi

    docker_network_build_args=(--network "$network")
    docker_network_run_args=(--network "$network")
}

# Build and packing containers write outputs as the host user.
enter_container_user() {
    if [[ "${DEV_ENV_CONTAINER_USER_READY:-}" != 1 ]]; then
        local host_uid="${DEV_ENV_HOST_UID:-}"
        local host_gid="${DEV_ENV_HOST_GID:-}"
        local group_entry build_group passwd_entry build_user passwd_gid

        case "$host_uid:$host_gid" in
            *[!0-9:]*|:*|*:)
                printf 'dev-env: invalid host UID/GID: %s:%s\n' "$host_uid" "$host_gid" >&2
                exit 2
                ;;
        esac

        if ((host_uid == 0)); then
            mkdir -p "$HOME"
            export DEV_ENV_CONTAINER_USER_READY=1
        else
            if group_entry="$(getent group "$host_gid")"; then
                build_group="${group_entry%%:*}"
            else
                build_group="devbuilder${host_gid}"
                groupadd --gid "$host_gid" "$build_group"
            fi

            if passwd_entry="$(getent passwd "$host_uid")"; then
                build_user="${passwd_entry%%:*}"
                passwd_gid="$(printf '%s\n' "$passwd_entry" | cut -d: -f4)"
                [[ "$passwd_gid" == "$host_gid" ]] || usermod --gid "$build_group" "$build_user"
            else
                build_user="devbuilder${host_uid}"
                useradd \
                    --uid "$host_uid" \
                    --gid "$build_group" \
                    --home-dir "$HOME" \
                    --no-create-home \
                    --shell /bin/bash \
                    "$build_user"
            fi

            mkdir -p "$HOME"
            chown "$host_uid:$host_gid" "$HOME"
            runuser --user "$build_user" --preserve-environment -- test -w "$HOME"
            export DEV_ENV_CONTAINER_USER_READY=1
            exec runuser --user "$build_user" --preserve-environment -- bash "$0" "$@"
        fi
    fi

}
