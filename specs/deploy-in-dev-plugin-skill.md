# Skill: Deploy the in-development plugin

## Purpose

Provide a project-local Codex skill that builds the current Decky OpenRGB
source and deploys the resulting plugin directory to `olympus` for development
testing.

## Requirements

1. Store the skill beneath `.agents/skills` and provide a directly executable
   bundled shell script.
2. Build `outputs.decky-openrgb` and obtain its output directory from the JSON
   emitted by `devenv build`; do not hard-code a Nix store path or expect a ZIP
   archive.
3. Copy the built directory to `~/Downloads/decky-openrgb` on `olympus`.
4. Replace `/var/lib/decky-loader/plugins/decky-openrgb` with the staged build,
   recursively set its ownership to `root:root`, and restart
   `decky-loader.service`.
5. Stop at the first failed command and clean stale remote staging before
   copying a new build.
6. Instruct Codex to obtain explicit authorization before running the script
   because it replaces a remote installation and restarts a service.
7. Execute the remote installation block explicitly with Bash so it does not
   depend on the remote account's Fish login shell syntax.

## Acceptance Criteria

- **DEPLOY-SKILL-001:** The skill has valid `SKILL.md` frontmatter, matching UI
  metadata, and an executable bundled deploy script.
- **DEPLOY-SKILL-002:** The script dynamically builds and selects the unpacked
  `outputs.decky-openrgb` directory without a hard-coded store path or `unzip`.
- **DEPLOY-SKILL-003:** The script stages the output on `olympus`, installs it
  with `root:root` ownership, and restarts `decky-loader.service`, with the
  installation block interpreted by Bash regardless of the login shell.
- **DEPLOY-SKILL-004:** The instructions require explicit deployment approval
  and faithful failure reporting.
