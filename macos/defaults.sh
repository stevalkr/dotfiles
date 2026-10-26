#!/usr/bin/env bash
set -euo pipefail

enable_remote_login=false
if [[ "${1:-}" == "--enable-remote-login" ]]; then
  enable_remote_login=true
elif [[ $# -gt 0 ]]; then
  echo "usage: $0 [--enable-remote-login]" >&2
  exit 2
fi

fish_path=$(command -v fish) || {
  echo 'Fish is required; install it before applying macOS defaults.' >&2
  exit 1
}
current_user=$(id -un)
current_shell=$(dscl . -read "/Users/$current_user" UserShell | sed 's/^UserShell: //')
register_fish=false
grep -Fxq "$fish_path" /etc/shells || register_fish=true

set_global_default() {
  local key=$1
  local type=$2
  local value=$3
  local expected=$4
  local current
  current=$(defaults read -g "$key" 2>/dev/null || true)
  if [[ "$current" != "$expected" ]]; then
    defaults write -g "$key" "$type" "$value"
  fi
}

set_global_default KeyRepeat -int 3 3
set_global_default InitialKeyRepeat -int 16 16
set_global_default AppleShowAllExtensions -bool true 1
set_global_default AppleSpacesSwitchOnActivate -bool false 0
set_global_default AppleInterfaceStyleSwitchesAutomatically -bool true 1

# systemsetup -get* requires root, so read state directly.
timezone=$(readlink /etc/localtime | sed 's|.*/zoneinfo/||')

need_sudo=false
$register_fish && need_sudo=true
[[ "$timezone" == 'Asia/Singapore' ]] || need_sudo=true
if $enable_remote_login; then
  remote_login=off
  launchctl print-disabled system | grep -Fq '"com.openssh.sshd" => enabled' && remote_login=on
  [[ "$remote_login" == on ]] || need_sudo=true
fi

if $need_sudo; then
  echo 'Administrator access is required for shell registration, timezone, or Remote Login changes.'
  sudo -v
fi

if $register_fish; then
  printf '%s\n' "$fish_path" | sudo tee -a /etc/shells >/dev/null
fi

if [[ "$current_shell" != "$fish_path" ]]; then
  chsh -s "$fish_path"
fi

if [[ "$timezone" != 'Asia/Singapore' ]]; then
  # systemsetup logs a harmless "Error:-99 ... InternetServices.m" on recent macOS.
  sudo systemsetup -settimezone Asia/Singapore >/dev/null 2>&1
fi

if $enable_remote_login && [[ "$remote_login" != on ]]; then
  sudo systemsetup -setremotelogin on >/dev/null
fi

echo 'macOS defaults are up to date.'
