# Feature: Automatically apply a profile

## Purpose

One optional setting reapplies the selected profile when the Decky plugin
backend starts and when Steam resumes from suspend.

## Requirements

1. Automatic application is disabled by default and is controlled by one
   persisted toggle for both startup and resume.
2. The toggle cannot be enabled without an available selected profile.
3. Backend startup is the boot trigger. It includes initial OS boot as well as
   Decky service or plugin restarts. The plugin must not install or manage a
   separate systemd unit.
4. After loading settings and scanning profiles during backend startup, begin an
   automatic startup application only when automation remains enabled and the
   selection remains available.
5. When Steam exposes a resume-from-suspend callback API, the frontend registers
   it during plugin initialization. On resume it asks the backend to apply only
   when automation is enabled, and the callback is unregistered when the plugin
   dismounts. When the API is unavailable, the frontend must still load and all
   functionality except the resume trigger remains available.
6. An automatic sequence attempts immediately. After a failed attempt, retry at
   five-second intervals up to three additional times, for at most four
   attempts total. Stop immediately after the first success.
7. Apply the 30-second per-attempt timeout from the application specification
   to every automatic attempt.
8. Use one backend synchronization boundary for all manual and automatic
   attempts so OpenRGB child processes never overlap.
9. If another resume request arrives while a resume sequence is queued or
   running, coalesce it into that sequence instead of queueing an additional
   sequence.
10. Unloading the backend cancels pending retry timers and prevents new child
    processes from starting.
11. Publish only the final result of an automatic sequence as Last result. Log
    individual attempt failures for diagnosis.

## Acceptance Criteria

- **AUTO-001:** Automation defaults off and cannot be enabled without an
  available selection.
- **AUTO-002:** With automation off, startup and resume launch no process.
- **AUTO-003:** With automation on, backend startup launches an automatic
  sequence after settings load and profile discovery; no systemd unit is used.
- **AUTO-004:** When supported, the frontend registers one resume callback,
  invokes the backend from it, and unregisters the callback on dismount. When
  unsupported, plugin initialization and dismount complete without error.
- **AUTO-005:** An initial success performs one attempt; repeated failures
  perform four attempts at five-second intervals; an intermediate success stops
  further retries.
- **AUTO-006:** Manual and automatic child processes never overlap.
- **AUTO-007:** Overlapping resume requests produce one resume sequence.
- **AUTO-008:** Backend unload cancels pending retries cleanly.
- **AUTO-009:** Only the final sequence result becomes Last result, while every
  failed attempt is logged.
