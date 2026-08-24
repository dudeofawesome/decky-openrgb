# Decky OpenRGB implementation tasks

Each task references the acceptance criteria it implements or verifies. A task
is complete only when its associated automated tests pass.

## 1. Backend foundations

- [x] Define persisted settings, profile summaries, plugin state, apply results,
      and trigger types. Implement safe default loading and atomic persistence.
      (`ARCH-002`, `UI-001`, `UI-002`)
- [x] Implement immediate, case-insensitive, non-recursive profile discovery,
      deterministic sorting, resolved default paths, the always-searched
      `/var/lib/OpenRGB` system path, and discovery errors.
      (`DISC-001`, `DISC-002`, `DISC-003`, `DISC-004`, `DISC-005`, `DISC-006`,
      `DISC-007`, `DISC-009`)
- [x] Reconcile selection after every successful scan and atomically clear a
      stale selection and automation setting. (`DISC-008`, `AUTO-001`)
- [x] Expose state, refresh, selection, and automation backend operations with
      validation and immediate persistence. (`DISC-005`, `UI-002`, `UI-006`)

## 2. Configuration and application

- [x] Implement advanced-setting validation and atomic explicit Save, followed
      by discovery against the newly resolved directory. (`UI-003`, `UI-004`)
- [x] Build local and remote OpenRGB argument vectors using the default or
      overridden executable and with shell execution disabled. (`APPLY-002`,
      `APPLY-003`, `APPLY-004`, `APPLY-009`)
- [x] Implement selection preconditions, captured output, the 30-second timeout,
      child termination, success-marker checking, diagnostic logging, and manual
      application. (`APPLY-001`, `APPLY-005`, `APPLY-006`, `APPLY-007`)
- [x] Track final Last result and successful Last applied independently and
      expose both through state. (`APPLY-008`)

## 3. Automation and lifecycle

- [x] Run enabled automation after backend startup settings load and discovery,
      without installing a systemd unit. (`AUTO-002`, `AUTO-003`)
- [x] Implement immediate automatic attempts plus three five-second retries,
      stop on success, log attempts, and publish only the final result.
      (`AUTO-005`, `AUTO-009`)
- [x] Serialize all apply attempts, coalesce overlapping resume sequences, and
      cancel pending retries on unload. (`AUTO-006`, `AUTO-007`, `AUTO-008`)
- [x] Register the Steam resume callback in the frontend when supported, call
      the backend, and unregister it and the settings route on dismount; keep the
      plugin usable when the callback API is absent. (`AUTO-004`, `UI-007`)

## 4. Frontend

- [x] Add Effect as a frontend runtime dependency and use it for backend
      interactions, expected errors, and asynchronous state transitions.
      (`ARCH-001`)
- [x] Replace the template panel with profile selection, Apply, Refresh,
      automation, inline result, Last applied, empty/error states, and settings
      navigation. (`UI-005`, `UI-006`, `UI-008`)
- [x] Add the dedicated settings route with draft fields, explicit Save,
      field-level validation errors, and post-save discovery state. (`UI-003`,
      `UI-004`, `UI-007`)
- [x] Implement notification policy: toast failures only and always update
      inline final state. (`UI-009`)
- [x] Use the Decky below-row button layout for Quick Access actions so their
      highlighted bounds remain inside the sidebar. (`UI-010`)

## 5. Automated tests

- [x] Test discovery with temporary directories: extension filtering, nested
      files, ordering, exact identifiers, default and system path resolution,
      empty/error paths, refresh triggers, and stale-selection reconciliation.
      (`DISC-001`, `DISC-002`, `DISC-003`, `DISC-004`, `DISC-005`, `DISC-006`,
      `DISC-007`, `DISC-008`, `DISC-009`)
- [x] Test settings defaults, malformed storage, round trips, validation,
      atomic Save, immediate main-control persistence, and rescan behavior.
      (`UI-001` through `UI-004`, `UI-006`)
- [x] Test application with fake executables: exact local/remote argv, spaces,
      default and overridden executables, success marker, exit failures, missing
      marker, launch failure, timeout termination, stale selection, and literal
      metacharacters. (`APPLY-001`, `APPLY-002`, `APPLY-003`, `APPLY-004`,
      `APPLY-005`, `APPLY-006`, `APPLY-007`, `APPLY-008`, `APPLY-009`)
- [x] Test automation with controlled clocks and fake processes: disabled
      triggers, startup, resume registration cleanup, retry timing and exhaustion,
      unsupported resume APIs, early success, serialization, coalescing, unload,
      and final-result publishing.
      (`AUTO-001`, `AUTO-002`, `AUTO-003`, `AUTO-004`, `AUTO-005`, `AUTO-006`,
      `AUTO-007`, `AUTO-008`, `AUTO-009`)
- [x] Test frontend loading, ready, applying, empty and error rendering; control
      enablement; route lifecycle; selected versus Last applied labels; and exact
      toast behavior. (`UI-005`, `UI-007` through `UI-009`)
- [x] Test that Quick Access actions use the below-row button layout required to
      prevent highlighted controls from overflowing the sidebar. (`UI-010`)
- [x] Run the complete automated suite and confirm every acceptance criterion
      above has a passing test before marking implementation complete.

## 6. Distribution

- [x] Add a reproducible devenv output that builds the frontend from the pnpm
      lockfile and creates an unpacked Decky plugin directory. (`DIST-001`)
- [x] Package the runtime frontend, Python backend, metadata, documentation,
      assets, and defaults directly in the plugin output root while excluding
      development files. (`DIST-002`, `DIST-003`)
- [x] Validate the generated output layout as part of the Nix build.
      (`DIST-002`, `DIST-003`)
- [x] Resolve backend modules relative to the file-loaded Decky entrypoint and
      cover loading when the plugin root is absent from Python's initial module
      search path. (`DIST-004`)
- [x] Export the unpacked plugin derivation as both the named and default root
      flake package for consumption by other flakes and NixOS configurations.
      (`DIST-005`)
- [x] Declare OpenRGB in the plugin package's runtime dependencies and have the
      NixOS module add the selected package's declared dependencies to Decky
      Loader's service path. (`DIST-006`)

## 7. Developer skills

- [x] Add and validate a script-backed project-local skill for retrieving the
      newest Decky OpenRGB plugin log from `olympus` without modifying the remote
      host.
      (`LOG-SKILL-001`, `LOG-SKILL-002`, `LOG-SKILL-003`)
- [x] Add and validate a script-backed project-local skill for building and
      deploying the in-development plugin to `olympus`.
      (`DEPLOY-SKILL-001`, `DEPLOY-SKILL-002`, `DEPLOY-SKILL-003`,
      `DEPLOY-SKILL-004`)

## Out of scope for v1

- Installing, bundling, launching as a persistent service, or upgrading OpenRGB.
- Creating, editing, renaming, deleting, importing, or exporting `.orp` files.
- Installing a systemd unit or querying OpenRGB for a guaranteed current profile.
- A formal manual hardware-validation checklist.
