# Skill: Get latest plugin logs

## Purpose

Provide a project-local Codex skill that retrieves the newest Decky OpenRGB
plugin log from the `olympus` host for inspection and diagnosis.

## Requirements

1. Store the skill beneath `.agents/skills` so it is discoverable in this
   project.
2. Provide a directly executable bundled shell script that retrieves the newest
   log by listing
   `/var/lib/decky-loader/logs/decky-openrgb`, sorting the filenames, selecting
   the last filename, and reading that file over SSH from `olympus`.
3. Instruct Codex to invoke the bundled script instead of reproducing the SSH
   command in the skill instructions.
4. The retrieval must be read-only and must not modify the remote host.
5. Report remote command failures faithfully and identify truncated output.

## Acceptance Criteria

- **LOG-SKILL-001:** The skill has valid `SKILL.md` frontmatter and matching UI
  metadata.
- **LOG-SKILL-002:** The skill contains an executable script with the specified
  `ssh olympus` retrieval command, and its instructions invoke that script.
- **LOG-SKILL-003:** The instructions prohibit remote mutation and require
  honest reporting of failures or truncation.
