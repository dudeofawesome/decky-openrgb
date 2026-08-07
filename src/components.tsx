import {
  ButtonItem,
  DropdownItem,
  Navigation,
  PanelSection,
  PanelSectionRow,
  TextField,
  ToggleField,
} from "@decky/ui";
import { Effect } from "effect";
import { useEffect, useMemo, useState } from "react";

import { useOpenRgb } from "./hooks";
import {
  AdvancedSettings,
  controller,
  FieldErrors,
  validateAdvancedSettings,
} from "./model";

export const SETTINGS_ROUTE = "/decky-openrgb/settings";

const messageStyle = { fontSize: "0.9em", margin: "6px 0", opacity: 0.85 };
const errorStyle = { ...messageStyle, color: "#ff6b6b" };

const ErrorMessage = ({ children }: { children: string | null | undefined }) =>
  children ? <div style={errorStyle}>{children}</div> : null;

const formatTimestamp = (timestamp: string): string => {
  const date = new Date(timestamp);
  return Number.isNaN(date.getTime()) ? timestamp : date.toLocaleString();
};

export function QuickAccess() {
  const view = useOpenRgb();
  const state = view.state;
  const unavailable = view.busy !== null;

  if (state === null) {
    return (
      <PanelSection title="OpenRGB Profiles">
        <PanelSectionRow>
          <div style={messageStyle}>
            {view.operationError ?? "Loading profiles…"}
          </div>
        </PanelSectionRow>
        {view.operationError ? (
          <PanelSectionRow>
            <ButtonItem onClick={() => void controller.initialize()}>Retry</ButtonItem>
          </PanelSectionRow>
        ) : null}
        <SettingsButton />
      </PanelSection>
    );
  }

  const selectedAvailable = state.profiles.some(
    (profile) => profile.identifier === state.settings.selected_profile,
  );

  return (
    <>
      <PanelSection title="OpenRGB Profiles">
        {state.settings_error ? (
          <PanelSectionRow>
            <ErrorMessage>{state.settings_error}</ErrorMessage>
          </PanelSectionRow>
        ) : null}
        {state.profiles.length > 0 ? (
          <PanelSectionRow>
            <DropdownItem
              label="Desired profile"
              description="Selecting a profile does not apply it."
              rgOptions={state.profiles.map((profile) => ({
                data: profile.identifier,
                label: profile.display_name,
              }))}
              selectedOption={state.settings.selected_profile}
              disabled={unavailable}
              strDefaultLabel="Choose a profile"
              onChange={(option) => void controller.select(String(option.data))}
            />
          </PanelSectionRow>
        ) : (
          <PanelSectionRow>
            <div style={state.discovery_error ? errorStyle : messageStyle}>
              {state.discovery_error
                ? `Profiles could not be discovered: ${state.discovery_error}`
                : "No OpenRGB profiles were found in the configured or system directory."}
            </div>
          </PanelSectionRow>
        )}
        {view.operationError ? (
          <PanelSectionRow>
            <ErrorMessage>{view.operationError}</ErrorMessage>
          </PanelSectionRow>
        ) : null}
        <PanelSectionRow>
          <ButtonItem
            disabled={unavailable || !selectedAvailable}
            onClick={() => void controller.applyManual()}
          >
            {view.busy === "applying" ? "Applying…" : "Apply"}
          </ButtonItem>
        </PanelSectionRow>
        <PanelSectionRow>
          <ButtonItem disabled={unavailable} onClick={() => void controller.refresh()}>
            {view.busy === "refreshing" ? "Refreshing…" : "Refresh"}
          </ButtonItem>
        </PanelSectionRow>
        <PanelSectionRow>
          <ToggleField
            label="Apply automatically"
            description="Apply the desired profile on backend startup and resume."
            checked={state.settings.automatic_apply}
            disabled={unavailable || !selectedAvailable}
            onChange={(enabled) => void controller.setAutomatic(enabled)}
          />
        </PanelSectionRow>
        <SettingsButton />
      </PanelSection>

      <PanelSection title="Status">
        <PanelSectionRow>
          <div style={messageStyle}>
            <strong>Last result:</strong>{" "}
            {state.last_result
              ? `${state.last_result.message} (${formatTimestamp(state.last_result.timestamp)})`
              : "No application attempted by this plugin yet."}
          </div>
        </PanelSectionRow>
        <PanelSectionRow>
          <div style={messageStyle}>
            <strong>Last applied by this plugin:</strong>{" "}
            {state.last_applied
              ? `${state.last_applied.profile} at ${formatTimestamp(state.last_applied.timestamp)}`
              : "None"}
            <div>This is historical and does not verify OpenRGB’s current state.</div>
          </div>
        </PanelSectionRow>
      </PanelSection>
    </>
  );
}

function SettingsButton() {
  return (
    <PanelSectionRow>
      <ButtonItem
        onClick={() => {
          Navigation.Navigate(SETTINGS_ROUTE);
          Navigation.CloseSideMenus();
        }}
      >
        Settings
      </ButtonItem>
    </PanelSectionRow>
  );
}

const blankDraft: AdvancedSettings = {
  executable_override: "",
  profiles_directory_override: "",
  remote_enabled: false,
  server_address: "",
};

export function SettingsPage() {
  const view = useOpenRgb();
  const saved = view.state?.settings;
  const savedDraft = useMemo<AdvancedSettings>(
    () =>
      saved
        ? {
            executable_override: saved.executable_override,
            profiles_directory_override: saved.profiles_directory_override,
            remote_enabled: saved.remote_enabled,
            server_address: saved.server_address,
          }
        : blankDraft,
    [saved],
  );
  const [draft, setDraft] = useState<AdvancedSettings>(savedDraft);
  const [errors, setErrors] = useState<FieldErrors>({});
  const [savedMessage, setSavedMessage] = useState<string | null>(null);

  useEffect(() => setDraft(savedDraft), [savedDraft]);

  const save = (): void => {
    setSavedMessage(null);
    void Effect.runPromise(validateAdvancedSettings(draft)).then((fieldErrors) => {
      setErrors(fieldErrors);
      if (Object.keys(fieldErrors).length > 0) return;
      void controller.save(draft).then(() => {
        const latest = controller.getSnapshot();
        if (latest.operationError === null) setSavedMessage("Settings saved.");
      });
    });
  };

  return (
    <div style={{ padding: "16px 24px", maxWidth: 900 }}>
      <PanelSection title="OpenRGB Settings">
        <PanelSectionRow>
          <TextField
            label="Executable override"
            description="Absolute path, or leave empty to resolve OpenRGB through PATH."
            value={draft.executable_override}
            disabled={view.busy === "saving"}
            onChange={(event) =>
              setDraft({ ...draft, executable_override: event.target.value })
            }
          />
          <ErrorMessage>{errors.executable_override}</ErrorMessage>
        </PanelSectionRow>
        <PanelSectionRow>
          <TextField
            label="Profiles directory override"
            description="Absolute path, or leave empty to use the Deck user default."
            value={draft.profiles_directory_override}
            disabled={view.busy === "saving"}
            onChange={(event) =>
              setDraft({ ...draft, profiles_directory_override: event.target.value })
            }
          />
          <ErrorMessage>{errors.profiles_directory_override}</ErrorMessage>
        </PanelSectionRow>
        <PanelSectionRow>
          <ToggleField
            label="Remote mode"
            checked={draft.remote_enabled}
            disabled={view.busy === "saving"}
            onChange={(remote_enabled) => setDraft({ ...draft, remote_enabled })}
          />
        </PanelSectionRow>
        <PanelSectionRow>
          <TextField
            label="Server address"
            description="Hostname or IP address, optionally followed by a port."
            value={draft.server_address}
            disabled={view.busy === "saving"}
            onChange={(event) => setDraft({ ...draft, server_address: event.target.value })}
          />
          <ErrorMessage>{errors.server_address}</ErrorMessage>
        </PanelSectionRow>
        {view.operationError ? (
          <PanelSectionRow>
            <ErrorMessage>{view.operationError}</ErrorMessage>
          </PanelSectionRow>
        ) : null}
        {savedMessage ? (
          <PanelSectionRow>
            <div style={messageStyle}>{savedMessage}</div>
          </PanelSectionRow>
        ) : null}
        {view.state?.discovery_error ? (
          <PanelSectionRow>
            <ErrorMessage>
              {`Saved, but profile discovery failed: ${view.state.discovery_error}`}
            </ErrorMessage>
          </PanelSectionRow>
        ) : null}
        <PanelSectionRow>
          <ButtonItem disabled={view.busy === "saving"} onClick={save}>
            {view.busy === "saving" ? "Saving…" : "Save"}
          </ButtonItem>
        </PanelSectionRow>
      </PanelSection>
    </div>
  );
}
