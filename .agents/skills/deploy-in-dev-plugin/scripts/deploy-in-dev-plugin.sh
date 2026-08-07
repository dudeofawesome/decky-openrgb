#!/usr/bin/env bash

set -euo pipefail

nix run nixpkgs#wakeonlan -- 'C8:7F:54:6A:3F:56'

script_directory="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repository_root="$(cd -- "$script_directory/../../../.." && pwd)"

cd "$repository_root"

build_result="$(devenv build outputs.decky-openrgb)"
plugin_output="$(
  printf '%s\n' "$build_result" |
    jq -er '."outputs.decky-openrgb"'
)"

if [[ ! -d "$plugin_output" ]]; then
  printf 'Build output is not a directory: %s\n' "$plugin_output" >&2
  exit 1
fi

ssh olympus -- 'rm -rf "/tmp/decky-openrgb-build"'
scp -r -- "$plugin_output" olympus:/tmp/decky-openrgb-build

ssh olympus -- bash -s <<'REMOTE_BASH'
set -eu

staged_plugin="/tmp/decky-openrgb-build"
installed_plugin="/var/lib/decky-loader/plugins/decky-openrgb"

sudo chown -R root:root "$staged_plugin"
sudo rm -rf "$installed_plugin"
sudo mv "$staged_plugin" "$installed_plugin"
sudo systemctl restart decky-loader.service
REMOTE_BASH
