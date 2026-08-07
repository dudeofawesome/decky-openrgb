#!/usr/bin/env bash

set -euo pipefail

nix run nixpkgs#wakeonlan -- 'C8:7F:54:6A:3F:56'

ssh olympus -- \
  'cat "/var/lib/decky-loader/logs/decky-openrgb/$(ls /var/lib/decky-loader/logs/decky-openrgb/ | sort | tail -1)"'
