import { describe, expect, it, vi } from "vitest";

const api = vi.hoisted(() => ({
  handlers: new Map<string, (...args: unknown[]) => Promise<unknown>>(),
  toast: vi.fn(),
}));

vi.mock("@decky/api", () => ({
  callable:
    (route: string) =>
    (...args: unknown[]) =>
      api.handlers.get(route)?.(...args) ?? Promise.reject(new Error(`No ${route} mock`)),
  toaster: { toast: api.toast },
}));

import { ApplyResult, controller, PluginState } from "./model";

const initialState = (): PluginState => ({
  settings: {
    selected_profile: "Blue.orp",
    automatic_apply: false,
    executable_override: "",
    profiles_directory_override: "",
    remote_enabled: false,
    server_address: "",
  },
  resolved_executable: "OpenRGB",
  resolved_profiles_directory: "/home/deck/.config/OpenRGB",
  profiles: [{ identifier: "Blue.orp", display_name: "Blue" }],
  discovery_error: null,
  settings_error: null,
  last_result: null,
  last_applied: null,
});

describe("OpenRGB Effect controller", () => {
  it("persists controls without applying and follows resume/toast policy", async () => {
    let state = initialState();
    const apply = vi.fn<(trigger: "manual" | "resume") => Promise<ApplyResult>>();
    api.handlers.set("get_state", async () => state);
    api.handlers.set("set_selected_profile", async (identifier) => {
      state = { ...state, settings: { ...state.settings, selected_profile: String(identifier) } };
      return state;
    });
    api.handlers.set("set_automatic_apply", async (enabled) => {
      state = { ...state, settings: { ...state.settings, automatic_apply: Boolean(enabled) } };
      return state;
    });
    api.handlers.set("apply_selected", (trigger) =>
      apply(trigger as "manual" | "resume"),
    );

    await controller.initialize();
    await controller.select("Blue.orp");
    expect(apply).not.toHaveBeenCalled();

    await controller.resume();
    expect(apply).not.toHaveBeenCalled();

    await controller.setAutomatic(true);
    let finishResume: ((result: ApplyResult) => void) | undefined;
    apply.mockReturnValueOnce(
      new Promise((resolve) => {
        finishResume = resolve;
      }),
    );
    const firstResume = controller.resume();
    const coalescedResume = controller.resume();
    expect(apply).toHaveBeenCalledTimes(1);
    finishResume?.({
      success: false,
      profile: "Blue.orp",
      trigger: "resume",
      timestamp: "2026-08-07T09:00:00Z",
      message: "Could not apply Blue.",
    });
    await Promise.all([firstResume, coalescedResume]);
    expect(api.toast).toHaveBeenCalledTimes(1);
    expect(controller.getSnapshot().state?.last_applied).toBeNull();

    apply.mockResolvedValueOnce({
      success: true,
      profile: "Blue.orp",
      trigger: "manual",
      timestamp: "2026-08-07T09:01:00Z",
      message: "Applied Blue.",
    });
    await controller.applyManual();
    expect(api.toast).toHaveBeenCalledTimes(1);
    expect(controller.getSnapshot().state?.last_applied).toEqual({
      profile: "Blue.orp",
      timestamp: "2026-08-07T09:01:00Z",
    });
  });
});
