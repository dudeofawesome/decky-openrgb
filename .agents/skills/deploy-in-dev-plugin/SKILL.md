---
name: deploy-in-dev-plugin
description: Build the current Decky OpenRGB development source and deploy it to the olympus host as the installed Decky plugin. Use when the user asks to deploy, install, push, or test the in-development plugin on olympus.
---

# Deploy In-Dev Plugin

Deploy only after the user explicitly authorizes replacing the installed plugin
and restarting Decky Loader on `olympus`.

## Deploy

Run the bundled script from the repository root:

```bash
.agents/skills/deploy-in-dev-plugin/scripts/deploy-in-dev-plugin.sh
```

Request permission if the execution environment requires approval for the Nix
build, network access, remote file replacement, or service restart. Do not
reproduce the deployment commands manually.

## Report the result

- On success, report that the build was installed and
  `decky-loader.service` was restarted.
- On failure, report the failing command and its actual output. Do not claim a
  partial deployment succeeded.
- Do not retry destructive remote steps automatically after a failure. Inspect
  the remote state or ask the user before retrying.
