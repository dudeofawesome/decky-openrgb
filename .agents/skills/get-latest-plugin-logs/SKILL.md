---
name: get-latest-plugin-logs
description: Fetch the newest Decky OpenRGB plugin log from the olympus host over SSH. Use when diagnosing plugin behavior, investigating a failure, checking recent runtime output, or whenever the user asks for the latest or most recent decky-openrgb plugin logs.
---

# Get Latest Plugin Logs

Fetch the newest remote log without modifying the host.

## Fetch the log

Run the bundled script from the repository root:

```bash
.agents/skills/get-latest-plugin-logs/scripts/get-latest-plugin-logs.sh
```

Request permission if the execution environment requires approval for SSH or
network access. Do not reproduce the SSH command manually or replace it with a
local log lookup.

## Handle the result

- Return or analyze the fetched log according to the user's request.
- Preserve error messages and stack traces when summarizing diagnostic output.
- State clearly if tool output was truncated; do not imply that a partial log is
  complete.
- If SSH, directory listing, or file reading fails, report the actual failure
  and do not infer log contents.
- Do not change files, services, or configuration on `olympus`.
- Do not save the log locally unless the user requests it.
