# Distribution packaging

## Purpose

The project exposes reproducible devenv and standard Nix flake package outputs
that can be distributed to and installed by Decky Loader without requiring a
local checkout or pre-built frontend files. The flake output can also be used
as an input while building a NixOS system.

## Requirements

1. `devenv build outputs.decky-openrgb` builds the frontend from the locked pnpm
   dependencies and produces an unpacked Decky plugin directory.
2. The output directory contains the built frontend, Python backend, metadata,
   license, readme, assets, and the contents of `defaults` directly, without a
   ZIP archive or an additional top-level directory.
3. Development-only inputs, tests, and frontend source files are excluded from
   the output directory.
4. The build validates the output layout before publishing it.
5. The Python entrypoint must resolve the packaged `py_modules` directory
   relative to `main.py` when Decky loads the entrypoint directly, without
   relying on the plugin directory being the process working directory or
   already present on Python's module search path.
6. The root flake must expose the same unpacked plugin derivation as
   `packages.<system>.decky-openrgb` and as the default package so another
   flake can consume it without importing project-internal Nix files.

## Acceptance Criteria

- **DIST-001:** Building `outputs.decky-openrgb` from a clean source produces an
  unpacked plugin directory without relying on a checked-in `dist` directory.
- **DIST-002:** The output root contains the required Decky runtime files,
  including `dist/index.js`, `main.py`, `py_modules`, `package.json`,
  `plugin.json`, and `LICENSE`, and does not contain a ZIP archive.
- **DIST-003:** The output excludes `src`, tests, dependency directories, and
  Nix development configuration.
- **DIST-004:** Loading the packaged `main.py` by file path succeeds when the
  plugin root is absent from Python's initial module search path.
- **DIST-005:** `nix build .#decky-openrgb` and `nix build .` select the plugin
  package, and evaluating the root flake exposes both package attributes for
  supported Linux NixOS systems.
