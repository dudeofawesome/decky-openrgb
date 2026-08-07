# Decky OpenRGB implementation tasks

Each task references the acceptance criteria it implements or verifies. A task
is complete only when its associated automated tests pass.

## 1. Backend foundations

- [x] Define persisted settings, profile summaries, plugin state, apply results,
  and trigger types. Implement safe default loading and atomic persistence.
  (`ARCH-002`, `UI-001`, `UI-002`)
- [ ] Implement immediate, case-insensitive, non-recursive profile discovery,
  deterministic sorting, resolved default paths, the always-searched
  `/var/lib/OpenRGB` system path, and discovery errors.
  (`DISC-001`, `DISC-002`, `DISC-003`, `DISC-004`, `DISC-005`, `DISC-006`,
  `DISC-007`, `DISC-009`)
- [ ] Reconcile selection after every successful scan and atomically clear a
  stale selection and automation setting. (`DISC-008`, `AUTO-001`)
- [ ] Expose state, refresh, selection, and automation backend operations with
  validation and immediate persistence. (`DISC-005`, `UI-002`, `UI-006`)

## 2. Configuration and application

- [ ] Implement advanced-setting validation and atomic explicit Save, followed
  by discovery against the newly resolved directory. (`UI-003`, `UI-004`)
- [ ] Build local and remote OpenRGB argument vectors using the default or
  overridden executable and with shell execution disabled. (`APPLY-002`,
  `APPLY-003`, `APPLY-004`, `APPLY-009`)
- [ ] Implement selection preconditions, captured output, the 30-second timeout,
  child termination, success-marker checking, diagnostic logging, and manual
  application. (`APPLY-001`, `APPLY-005`, `APPLY-006`, `APPLY-007`)
- [ ] Track final Last result and successful Last applied independently and
  expose both through state. (`APPLY-008`)

## 3. Automation and lifecycle

- [ ] Run enabled automation after backend startup settings load and discovery,
  without installing a systemd unit. (`AUTO-002`, `AUTO-003`)
- [ ] Implement immediate automatic attempts plus three five-second retries,
  stop on success, log attempts, and publish only the final result.
  (`AUTO-005`, `AUTO-009`)
- [ ] Serialize all apply attempts, coalesce overlapping resume sequences, and
  cancel pending retries on unload. (`AUTO-006`, `AUTO-007`, `AUTO-008`)
- [ ] Register the Steam resume callback in the frontend, call the backend, and
  unregister it and the settings route on dismount. (`AUTO-004`, `UI-007`)

## 4. Frontend

- [ ] Add Effect as a frontend runtime dependency and use it for backend
  interactions, expected errors, and asynchronous state transitions.
  (`ARCH-001`)
- [ ] Replace the template panel with profile selection, Apply, Refresh,
  automation, inline result, Last applied, empty/error states, and settings
  navigation. (`UI-005`, `UI-006`, `UI-008`)
- [ ] Add the dedicated settings route with draft fields, explicit Save,
  field-level validation errors, and post-save discovery state. (`UI-003`,
  `UI-004`, `UI-007`)
- [ ] Implement notification policy: toast failures only and always update
  inline final state. (`UI-009`)

## 5. Automated tests

- [ ] Test discovery with temporary directories: extension filtering, nested
  files, ordering, exact identifiers, default and system path resolution,
  empty/error paths, refresh triggers, and stale-selection reconciliation.
  (`DISC-001`, `DISC-002`, `DISC-003`, `DISC-004`, `DISC-005`, `DISC-006`,
  `DISC-007`, `DISC-008`, `DISC-009`)
- [ ] Test settings defaults, malformed storage, round trips, validation,
  atomic Save, immediate main-control persistence, and rescan behavior.
  (`UI-001` through `UI-004`, `UI-006`)
- [ ] Test application with fake executables: exact local/remote argv, spaces,
  default and overridden executables, success marker, exit failures, missing
  marker, launch failure, timeout termination, stale selection, and literal
  metacharacters. (`APPLY-001`, `APPLY-002`, `APPLY-003`, `APPLY-004`,
  `APPLY-005`, `APPLY-006`, `APPLY-007`, `APPLY-008`, `APPLY-009`)
- [ ] Test automation with controlled clocks and fake processes: disabled
  triggers, startup, resume registration cleanup, retry timing and exhaustion,
  early success, serialization, coalescing, unload, and final-result publishing.
  (`AUTO-001`, `AUTO-002`, `AUTO-003`, `AUTO-004`, `AUTO-005`, `AUTO-006`,
  `AUTO-007`, `AUTO-008`, `AUTO-009`)
- [ ] Test frontend loading, ready, applying, empty and error rendering; control
  enablement; route lifecycle; selected versus Last applied labels; and exact
  toast behavior. (`UI-005`, `UI-007` through `UI-009`)
- [ ] Run the complete automated suite and confirm every acceptance criterion
  above has a passing test before marking implementation complete.

## Out of scope for v1

- Installing, bundling, launching as a persistent service, or upgrading OpenRGB.
- Creating, editing, renaming, deleting, importing, or exporting `.orp` files.
- Installing a systemd unit or querying OpenRGB for a guaranteed current profile.
- A formal manual hardware-validation checklist.
