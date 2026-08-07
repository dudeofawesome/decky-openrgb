import { Effect } from "effect";
import { describe, expect, it } from "vitest";

import { AdvancedSettings, validateAdvancedSettings } from "./validation";

const validDraft = (overrides: Partial<AdvancedSettings> = {}): AdvancedSettings => ({
  executable_override: "",
  profiles_directory_override: "",
  remote_enabled: false,
  server_address: "",
  ...overrides,
});

const validate = (draft: AdvancedSettings) =>
  Effect.runSync(validateAdvancedSettings(draft));

describe("advanced settings validation", () => {
  it("accepts empty overrides and ignores the server while remote mode is off", () => {
    expect(validate(validDraft({ server_address: "not a server address" }))).toEqual({});
  });

  it("requires absolute override paths", () => {
    expect(
      validate(
        validDraft({
          executable_override: "OpenRGB.AppImage",
          profiles_directory_override: "profiles",
        }),
      ),
    ).toEqual({
      executable_override: "Executable override must be an absolute path.",
      profiles_directory_override: "Profiles directory override must be an absolute path.",
    });
  });

  it.each([
    "openrgb.local",
    "openrgb.local.",
    "openrgb.local:6742",
    "192.168.1.10",
    "192.168.1.10:1",
    "[2001:db8::1]",
    "[2001:db8::1]:65535",
  ])("accepts remote server address %s", (server_address) => {
    expect(validate(validDraft({ remote_enabled: true, server_address }))).toEqual({});
  });

  it.each([
    "",
    "host name",
    "host:0",
    "host:65536",
    "host:abc",
    "bad..host",
    ":::",
    "[2001:db8::1]:0",
    "[2001:::1]",
  ])(
    "rejects remote server address %s",
    (server_address) => {
      expect(
        validate(validDraft({ remote_enabled: true, server_address })).server_address,
      ).toBeDefined();
    },
  );
});
