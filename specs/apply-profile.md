# Feature: Apply a selected OpenRGB profile

## Purpose

The plugin applies an existing local profile by launching an external OpenRGB
executable. OpenRGB is an external prerequisite and is not downloaded,
installed, upgraded, or bundled by the plugin.

## Command Contract

The backend must launch OpenRGB directly with an argument vector and with shell
execution disabled.

For local mode, the effective command is:

```text
<executable> --config <profiles-directory> --profile <profile-identifier>
```

For remote mode, the effective command is:

```text
<executable> --client <server-address> --config <profiles-directory> --profile <profile-identifier>
```

- `<executable>` is `OpenRGB` when the executable override is empty; otherwise
  it is the saved absolute override.
- `<profiles-directory>` is the resolved configured profiles directory.
- `<profile-identifier>` is the selected exact filename, not its display name
  or an absolute profile path.
- `<server-address>` is passed unchanged. OpenRGB supplies its default port,
  `6742`, when the saved address has no port.

## Requirements

1. Selection alone must never launch OpenRGB. Only the explicit **Apply** action
   or an enabled automatic trigger may do so.
2. Reject an apply request before launching a process when no profile is
   selected or the selected identifier is not in the latest discovered list.
3. Capture standard output and standard error and enforce a 30-second timeout
   for each process attempt. Terminate a timed-out child process.
4. An attempt succeeds only when the process exits with status zero and its
   standard output contains `Profile loaded successfully`.
5. A non-zero exit, missing success marker, launch error, or timeout is a
   failure. Expose a concise message to the UI and write diagnostic process
   output to the plugin log.
6. Maintain two distinct state values:
   - **Last result:** the most recent final manual or automatic result, whether
     successful or failed.
   - **Last applied:** the profile and timestamp from the most recent successful
     application by this plugin. A later failure does not erase it.
7. Do not claim that Last applied is OpenRGB's current state; another process
   may have changed the active lighting after the recorded application.
8. Manual applications make one attempt and do not use the automatic retry
   policy.

## Apply Result

Every final result contains:

- `success`: boolean;
- `profile`: exact selected profile identifier;
- `trigger`: `manual`, `startup`, or `resume`;
- `timestamp`: an ISO 8601 UTC timestamp;
- `message`: a concise, user-facing success or failure description.

## Acceptance Criteria

- **APPLY-001:** Selecting a profile persists the identifier without spawning a
  process; activating Apply spawns exactly one attempt.
- **APPLY-002:** Local mode constructs the exact argument vector in the local
  command contract, including filenames and paths containing spaces.
- **APPLY-003:** Remote mode adds exactly `--client <server-address>` and does
  not split or shell-interpret the saved address or any path.
- **APPLY-004:** The default executable resolves through `PATH`, while an
  absolute override is invoked directly.
- **APPLY-005:** Exit status zero plus the success marker records success;
  non-zero exit, absent marker, launch failure, and timeout record failure.
- **APPLY-006:** A timed-out child is terminated after 30 seconds.
- **APPLY-007:** Apply is rejected without a process when selection is empty or
  stale.
- **APPLY-008:** Last result tracks every final result, while Last applied
  changes only after success and is labeled as historical rather than current.
- **APPLY-009:** Metacharacters in settings or filenames are passed as literal
  arguments and cannot execute additional shell commands.
