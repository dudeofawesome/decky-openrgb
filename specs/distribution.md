# Distribution packaging

## Purpose

The project exposes a reproducible devenv build output that can be distributed
to and installed by Decky Loader without requiring a local checkout or
pre-built frontend files.

## Requirements

1. `devenv build outputs.plugin` builds the frontend from the locked pnpm
   dependencies and produces a versioned ZIP archive.
2. The archive contains one top-level `decky-openrgb` directory with the built
   frontend, Python backend, metadata, license, readme, assets, and the contents
   of `defaults`.
3. Development-only inputs, tests, and frontend source files are excluded from
   the archive.
4. The build validates the archive layout before publishing the output.

## Acceptance Criteria

- **DIST-001:** Building `outputs.plugin` from a clean source produces
  `decky-openrgb-<package-version>.zip` without relying on a checked-in `dist`
  directory.
- **DIST-002:** The ZIP has the required Decky runtime files beneath its single
  `decky-openrgb` root, including `dist/index.js`, `main.py`, `py_modules`,
  `package.json`, `plugin.json`, and `LICENSE`.
- **DIST-003:** The ZIP excludes `src`, tests, dependency directories, and Nix
  development configuration.
