# Feature: Settings, state, and Decky UI

## Persisted Settings

Persist settings in Decky's plugin settings directory with these logical
fields:

| Field | Type | Default | Meaning |
| --- | --- | --- | --- |
| `selected_profile` | string or null | null | Exact profile identifier |
| `automatic_apply` | boolean | false | Apply on backend startup and resume |
| `executable_override` | string | empty | Absolute executable path; empty uses `OpenRGB` from `PATH` |
| `profiles_directory_override` | string | empty | Absolute directory; empty uses the Deck user default |
| `remote_enabled` | boolean | false | Add the OpenRGB `--client` argument |
| `server_address` | string | empty | Remote host or host and port |

Missing or malformed settings files must fall back to defaults without
preventing the plugin UI from loading. Log the failure and expose a concise
settings error.

## Backend Interface

The frontend-facing backend API must provide operations equivalent to:

- `get_state()` returns settings, resolved paths, profiles, discovery/settings
  errors, Last result, and Last applied.
- `refresh_profiles()` rescans and returns the updated state.
- `set_selected_profile(identifier | null)` validates against the current list,
  persists the selection immediately, and never applies it.
- `set_automatic_apply(enabled)` enforces the selection precondition and
  persists immediately.
- `save_advanced_settings(draft)` validates and atomically persists the four
  advanced fields, then rescans profiles.
- `apply_selected(trigger)` accepts `manual` or `resume` from the frontend and
  returns the final Apply result. Startup uses the same internal application
  path without a frontend call.

Profiles returned in state contain exact `identifier` and `display_name`
values. Apply results use the shape defined in `apply-profile.md`.

## Advanced Settings Validation

1. An empty executable override is valid. A non-empty value must be an absolute
   path. Existence and executability are checked when applying so removable or
   temporarily unavailable paths can still be saved.
2. An empty profiles-directory override is valid. A non-empty value must be an
   absolute path. Directory availability is reported by discovery after Save.
3. When remote mode is enabled, server address is required and must contain no
   whitespace. It accepts a hostname or IP address with an optional decimal
   port from 1 through 65535. A bracketed IPv6 address may be followed by a
   port. When remote mode is disabled, the address may be empty and is not used.
4. Validation errors leave all persisted advanced settings unchanged and are
   shown beside the relevant field.
5. A successful Save persists all advanced fields atomically and rescans using
   the newly resolved directory. If that scan removes the selected profile, the
   discovery specification clears selection and disables automation.

## User Interface

### Quick Access panel

1. Show a loading state until initial state and profiles are available.
2. Show a profile selector using display names, an explicit **Apply** action, a
   **Refresh** action, the single automation toggle, inline status, and a
   navigation action for Settings.
3. Disable Apply while loading/applying or when no available profile is
   selected. Disable the automation toggle until a profile is available.
4. Show distinct empty-directory and discovery-error states. Both retain access
   to Refresh and Settings.
5. Label the dropdown as the selected or desired profile. Show Last applied
   separately with its profile and timestamp, explicitly as the last action by
   this plugin rather than OpenRGB's verified current state.

### Settings page

1. Use a dedicated Decky route containing editable drafts for executable
   override, profiles-directory override, remote toggle, and server address.
2. Changes do not affect persisted settings or runtime behavior until the user
   activates **Save**.
3. Show validation and save errors without leaving the page. After a successful
   Save, show the saved state and updated discovery outcome.

### Notifications

1. Always update inline Last result after a final result.
2. Show a toast for a failed manual application and for the final failure of an
   automatic sequence.
3. Do not show a toast for successful manual or automatic applications.

## Acceptance Criteria

- **UI-001:** Defaults and every persisted field round-trip through backend
  restart; malformed storage falls back safely and reports an error.
- **UI-002:** The backend operations expose the specified state and enforce
  selection, automation, validation, persistence, and trigger rules.
- **UI-003:** Invalid advanced drafts show field errors and change no persisted
  value; valid Save is atomic and initiates profile discovery.
- **UI-004:** Advanced edits remain drafts until explicit Save.
- **UI-005:** The Quick Access panel covers loading, ready, empty, discovery
  error, and applying states with correct control enablement.
- **UI-006:** Selection and automation changes persist immediately, while
  selection never applies a profile.
- **UI-007:** Settings navigation opens the dedicated route, and dismount removes
  the route.
- **UI-008:** Selected profile and Last applied are presented as distinct
  concepts with no assertion of OpenRGB's current state.
- **UI-009:** Manual failures and final automatic failures toast; successes do
  not; every final result appears inline.
