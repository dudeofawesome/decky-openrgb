// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { ViewState } from "./model";

const mocks = vi.hoisted(() => ({
  view: null as ViewState | null,
  applyManual: vi.fn(),
  initialize: vi.fn(),
  refresh: vi.fn(),
  save: vi.fn(async () => undefined),
  select: vi.fn(),
  setAutomatic: vi.fn(),
  navigate: vi.fn(),
  closeSideMenus: vi.fn(),
}));

vi.mock("./hooks", () => ({ useOpenRgb: () => mocks.view }));

vi.mock("./model", async () => {
  const { Effect } = await import("effect");
  return {
    controller: {
      applyManual: mocks.applyManual,
      getSnapshot: () => ({ ...mocks.view, operationError: null }),
      initialize: mocks.initialize,
      refresh: mocks.refresh,
      save: mocks.save,
      select: mocks.select,
      setAutomatic: mocks.setAutomatic,
    },
    validateAdvancedSettings: () => Effect.succeed({}),
  };
});

vi.mock("@decky/ui", () => ({
  ButtonItem: ({
    children,
    disabled,
    onClick,
  }: {
    children: ReactNode;
    disabled?: boolean;
    onClick?: () => void;
  }) => (
    <button disabled={disabled} onClick={onClick}>
      {children}
    </button>
  ),
  DropdownItem: ({
    disabled,
    label,
    onChange,
    rgOptions,
    selectedOption,
  }: {
    disabled?: boolean;
    label: string;
    onChange: (option: { data: string; label: string }) => void;
    rgOptions: { data: string; label: string }[];
    selectedOption: string | null;
  }) => (
    <label>
      {label}
      <select
        aria-label={label}
        disabled={disabled}
        value={selectedOption ?? ""}
        onChange={(event) => {
          const option = rgOptions.find(
            (candidate) => candidate.data === event.target.value,
          );
          if (option) onChange(option);
        }}
      >
        <option value="">Choose a profile</option>
        {rgOptions.map((option) => (
          <option key={option.data} value={option.data}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  ),
  Navigation: {
    Navigate: mocks.navigate,
    CloseSideMenus: mocks.closeSideMenus,
  },
  PanelSection: ({ children, title }: { children: ReactNode; title: string }) => (
    <section aria-label={title}>{children}</section>
  ),
  PanelSectionRow: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  TextField: ({
    disabled,
    label,
    onChange,
    value,
  }: {
    disabled?: boolean;
    label: string;
    onChange: (event: { target: { value: string } }) => void;
    value: string;
  }) => (
    <label>
      {label}
      <input
        aria-label={label}
        disabled={disabled}
        value={value}
        onChange={onChange}
      />
    </label>
  ),
  ToggleField: ({
    checked,
    disabled,
    label,
    onChange,
  }: {
    checked: boolean;
    disabled?: boolean;
    label: string;
    onChange: (checked: boolean) => void;
  }) => (
    <label>
      {label}
      <input
        aria-label={label}
        checked={checked}
        disabled={disabled}
        type="checkbox"
        onChange={(event) => onChange(event.target.checked)}
      />
    </label>
  ),
}));

import { QuickAccess, SETTINGS_ROUTE, SettingsPage } from "./components";

const readyView = (): ViewState => ({
  busy: null,
  operationError: null,
  state: {
    settings: {
      selected_profile: "Blue.orp",
      automatic_apply: true,
      executable_override: "",
      profiles_directory_override: "",
      remote_enabled: false,
      server_address: "",
    },
    resolved_executable: "openrgb",
    resolved_profiles_directory: "/home/deck/.config/OpenRGB",
    profiles: [{ identifier: "Blue.orp", display_name: "Blue" }],
    discovery_error: null,
    settings_error: null,
    last_result: {
      success: true,
      profile: "Blue.orp",
      trigger: "manual",
      timestamp: "2026-08-07T09:00:00Z",
      message: "Profile applied.",
    },
    last_applied: {
      profile: "Blue.orp",
      timestamp: "2026-08-07T09:00:00Z",
    },
  },
});

beforeEach(() => {
  vi.clearAllMocks();
  mocks.view = readyView();
});

afterEach(cleanup);

describe("Quick Access states", () => {
  it("renders loading and retry states while retaining Settings access", () => {
    mocks.view = { busy: "loading", operationError: null, state: null };
    const { rerender } = render(<QuickAccess />);
    expect(screen.getByText("Loading profiles…")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Settings" })).toBeTruthy();

    mocks.view = { busy: null, operationError: "Backend unavailable.", state: null };
    rerender(<QuickAccess />);
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    expect(mocks.initialize).toHaveBeenCalledOnce();
  });

  it("separates desired profile, inline result, and historical Last applied", () => {
    render(<QuickAccess />);
    expect(screen.getByLabelText("Desired profile")).toBeTruthy();
    expect(screen.getByText(/Profile applied/)).toBeTruthy();
    expect(screen.getByText(/Last applied by this plugin/)).toBeTruthy();
    expect(screen.getByText(/does not verify OpenRGB’s current state/)).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Apply" }));
    expect(mocks.applyManual).toHaveBeenCalledOnce();
    fireEvent.click(screen.getByRole("button", { name: "Settings" }));
    expect(mocks.navigate).toHaveBeenCalledWith(SETTINGS_ROUTE);
  });

  it("distinguishes empty discovery from errors and disables unavailable controls", () => {
    mocks.view = readyView();
    mocks.view.state = {
      ...mocks.view.state!,
      profiles: [],
      settings: { ...mocks.view.state!.settings, selected_profile: null },
    };
    const { rerender } = render(<QuickAccess />);
    expect(screen.getByText(/No OpenRGB profiles were found/)).toBeTruthy();
    expect(
      (screen.getByRole("button", { name: "Apply" }) as HTMLButtonElement).disabled,
    ).toBe(true);
    expect(
      (screen.getByLabelText("Apply automatically") as HTMLInputElement).disabled,
    ).toBe(true);

    mocks.view.state = {
      ...mocks.view.state,
      discovery_error: "Permission denied.",
    };
    rerender(<QuickAccess />);
    expect(screen.getByText(/Permission denied/)).toBeTruthy();
  });

  it("disables Apply and Refresh while applying", () => {
    mocks.view = { ...readyView(), busy: "applying" };
    render(<QuickAccess />);
    expect(
      (screen.getByRole("button", { name: "Applying…" }) as HTMLButtonElement)
        .disabled,
    ).toBe(true);
    expect(
      (screen.getByRole("button", { name: "Refresh" }) as HTMLButtonElement)
        .disabled,
    ).toBe(true);
  });
});

describe("Settings drafts", () => {
  it("keeps edits local until explicit Save", async () => {
    render(<SettingsPage />);
    fireEvent.change(screen.getByLabelText("Executable override"), {
      target: { value: "/opt/OpenRGB" },
    });
    expect(mocks.save).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    await waitFor(() =>
      expect(mocks.save).toHaveBeenCalledWith(
        expect.objectContaining({ executable_override: "/opt/OpenRGB" }),
      ),
    );
    expect(await screen.findByText("Settings saved.")).toBeTruthy();
  });
});
