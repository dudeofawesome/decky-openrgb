# Feature: Discover OpenRGB profiles

## Purpose

The plugin lists existing OpenRGB profile files so a user can select a desired
profile from Decky's Quick Access menu. Profile creation and file management are
outside this feature.

## Definitions

- The **configured profiles directory** is the saved directory override, or
  `<deck-user-home>/.config/OpenRGB` when the override is empty.
- The **system profiles directory** is always `/var/lib/OpenRGB`, regardless of
  the configured profiles directory.
- A **profile identifier** is the exact filename, including its `.orp`
  extension and original capitalization.
- A **profile display name** is the profile identifier with its final `.orp`
  extension removed.

## Requirements

1. Resolve the default directory from Decky's user-home value, not from the
   backend process's user or `~` expansion.
2. Scan the immediate children of both the configured profiles directory and
   the system profiles directory. If both resolve to the same directory, scan
   it only once.
3. Include directory entries that are files and whose final extension equals
   `.orp` case-insensitively. Do not inspect file contents to determine whether
   an entry is a profile.
4. Return both the exact profile identifier and its display name.
5. Sort profiles by display name case-insensitively, using the exact identifier
   as a deterministic tie-breaker.
6. Scan when the plugin loads, after a different profiles directory is saved,
   and when the user activates **Refresh**.
7. Treat a missing, non-directory, or unreadable configured path as an empty
   profile list with a user-facing discovery error. The plugin must remain
   usable so the user can open settings or retry Refresh.
8. Treat a readable directory containing no matching files as a successful,
   empty result rather than an error.
9. After every successful scan, if the persisted selected identifier is not in
   the result, clear the selection. When this happens, also disable automatic
   application and persist both changes. Never select another profile
   implicitly.

## Acceptance Criteria

- **DISC-001:** With mixed files and directories, only immediate-child files
  ending in `.orp` with any capitalization are returned.
- **DISC-002:** Nested profiles are excluded.
- **DISC-003:** Results expose exact filenames as identifiers, extension-free
  display names, and deterministic case-insensitive ordering.
- **DISC-004:** The default path is based on Decky's user home and resolves to
  `.config/OpenRGB` beneath it.
- **DISC-005:** Plugin load, a saved directory change, and Refresh each initiate
  a new scan.
- **DISC-006:** Missing and unreadable paths produce an empty list and a clear
  error without crashing.
- **DISC-007:** An empty readable directory produces an empty list with no
  discovery error.
- **DISC-008:** A missing saved selection is cleared, automation is disabled,
  and both changes are persisted; an available selection is preserved.
- **DISC-009:** Profiles are always searched for in `/var/lib/OpenRGB` in
  addition to the configured profiles directory, without scanning the same
  directory twice when both paths are equal.
