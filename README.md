# Decky OpenRGB

A [Decky Loader](https://decky.xyz/) plugin for applying existing [OpenRGB](https://openrgb.org/) profiles from Steam's Quick Access menu.

## Features

- Discovers `.orp` profiles in the configured OpenRGB directory and `/var/lib/OpenRGB`.
- Applies a selected profile on demand without changing it merely by selecting it.
- Optionally reapplies the selected profile when the Decky backend starts or Steam resumes from suspend.
- Supports a custom OpenRGB executable, a custom profiles directory, and a remote OpenRGB server.
- Shows the most recent apply result and the last profile successfully applied by the plugin.

OpenRGB must already be installed and available as `openrgb` on Decky's `PATH`, unless an absolute executable path is configured in the plugin's settings. The plugin uses existing profiles; it does not create or manage them.

## Installation

This plugin cannot currently be published to the official Decky Plugin Store because it was developed with AI. See Decky's [plugin submission policy](https://wiki.deckbrew.xyz/en/plugin-dev/submitting-plugins) for details.

For NixOS systems, this repository exposes both a `decky-openrgb` flake package and a NixOS module at `nixosModules.default`. The module provides `jovian.decky-loader.modules.openrgb.enable` and adds OpenRGB to the Decky Loader service environment.

To build the unpacked Decky plugin directory:

```bash
nix build .#decky-openrgb
```

The build output can then be installed through your Decky Loader configuration or copied into Decky's plugins directory for local use.

## Development

Enter the development environment and install the locked frontend dependencies:

```bash
devenv shell
```

Build the frontend and run its tests:

```bash
pnpm build
pnpm test
```

Run the backend test suite from the development environment:

```bash
pytest
```

Build the complete distributable plugin with:

```bash
devenv build outputs.decky-openrgb
```
