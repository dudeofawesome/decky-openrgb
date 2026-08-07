// @vitest-environment jsdom

import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({
  addRoute: vi.fn(),
  initialize: vi.fn(),
  registerResume: vi.fn(),
  removeRoute: vi.fn(),
  resume: vi.fn(),
  shutdown: vi.fn(),
  unregister: vi.fn(),
}));

vi.mock("@decky/api", () => ({
  definePlugin: (factory: () => unknown) => factory,
  routerHook: { addRoute: mocks.addRoute, removeRoute: mocks.removeRoute },
}));

vi.mock("@decky/ui", () => ({ staticClasses: { Title: "title" } }));
vi.mock("react-icons/fa", () => ({ FaLightbulb: () => null }));
vi.mock("./components", () => ({
  QuickAccess: () => null,
  SETTINGS_ROUTE: "/decky-openrgb/settings",
  SettingsPage: () => null,
}));
vi.mock("./model", () => ({
  controller: {
    initialize: mocks.initialize,
    resume: mocks.resume,
    shutdown: mocks.shutdown,
  },
}));

beforeEach(() => {
  vi.clearAllMocks();
  mocks.registerResume.mockReturnValue({ unregister: mocks.unregister });
  Object.assign(globalThis, {
    SteamClient: {
      System: { RegisterForOnResumeFromSuspend: mocks.registerResume },
    },
  });
});

describe("Decky lifecycle", () => {
  it("registers and removes the settings route and resume callback", async () => {
    vi.resetModules();
    const { default: createPlugin } = await import("./index");
    const plugin = createPlugin();

    expect(mocks.addRoute).toHaveBeenCalledOnce();
    expect(mocks.registerResume).toHaveBeenCalledOnce();
    expect(mocks.initialize).toHaveBeenCalledOnce();

    const callback = mocks.registerResume.mock.calls[0][0] as () => void;
    callback();
    expect(mocks.resume).toHaveBeenCalledOnce();

    plugin.onDismount?.();
    expect(mocks.shutdown).toHaveBeenCalledOnce();
    expect(mocks.unregister).toHaveBeenCalledOnce();
    expect(mocks.removeRoute).toHaveBeenCalledWith("/decky-openrgb/settings");
  });

  it("loads and dismounts when Steam has no resume callback API", async () => {
    Object.assign(globalThis, { SteamClient: { System: {} } });
    vi.resetModules();
    const { default: createPlugin } = await import("./index");
    const plugin = createPlugin();

    expect(mocks.addRoute).toHaveBeenCalledOnce();
    expect(mocks.initialize).toHaveBeenCalledOnce();
    expect(mocks.registerResume).not.toHaveBeenCalled();

    expect(() => plugin.onDismount?.()).not.toThrow();
    expect(mocks.shutdown).toHaveBeenCalledOnce();
    expect(mocks.unregister).not.toHaveBeenCalled();
    expect(mocks.removeRoute).toHaveBeenCalledWith("/decky-openrgb/settings");
  });
});
