# Distribution packaging

## Purpose

The project exposes reproducible devenv and standard Nix flake package and module outputs that can be distributed to NixOS systems.

## Requirements

### Package

1. `devenv build outputs.decky-openrgb` builds the frontend from the locked pnpm dependencies and produces an unpacked Decky plugin directory.
2. The package output directory contains the built frontend, Python backend, metadata, license, readme, and assets, without a ZIP archive or an additional top-level directory.
3. Development-only inputs, tests, and frontend source files are excluded from the output directory.
4. The build validates the output layout before publishing it.
5. The Python entrypoint must resolve the packaged `py_modules` directory relative to `main.py` when Decky loads the entrypoint directly, without relying on the plugin directory being the process working directory or already present on Python's module search path.
6. The root flake must expose the same unpacked plugin derivation as `packages.<system>.decky-openrgb` and as the default package so another flake can consume it without importing project-internal Nix files.

### Module

1. Expose the module in `nixosModules`.
2. Add `jovian.decky-loader.modules.openrgb` with:
   - an enable option;
   - a Decky plugin package option defaulting to `decky-openrgb`;
   - an OpenRGB executable package option defaulting to `openrgb`.
3. When enabled, add the selected OpenRGB executable package to the Decky Loader service path.
4. When disabled, do not install the plugin or modify the Decky Loader service path.
5. Evaluation must succeed when the module is imported with its required parent Decky Loader module.

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
- **NIXOS-001:** Evaluating the flake exposes `nixosModules.default` as a valid NixOS module.
- **NIXOS-002:** With the OpenRGB module disabled, the Decky OpenRGB plugin is absent from `jovian.decky-loader.plugins` and OpenRGB is not added to the Decky Loader service path.
- **NIXOS-003:** Enabling the module adds the configured OpenRGB executable
  package to `systemd.services.decky-loader.path`.
- **NIXOS-004:** The enabled configuration evaluates without option type errors.
