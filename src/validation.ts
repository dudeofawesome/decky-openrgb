import { Effect } from "effect";

export interface AdvancedSettings {
  executable_override: string;
  profiles_directory_override: string;
  remote_enabled: boolean;
  server_address: string;
}

export interface FieldErrors {
  executable_override?: string;
  profiles_directory_override?: string;
  server_address?: string;
}

const absolutePathError = (value: string, label: string): string | undefined =>
  value !== "" && !value.startsWith("/") ? `${label} must be an absolute path.` : undefined;

const validPort = (value: string | undefined): boolean => {
  if (value === undefined) return true;
  if (!/^\d+$/.test(value)) return false;
  const port = Number(value);
  return port >= 1 && port <= 65535;
};

const validIpv4 = (value: string): boolean => {
  const parts = value.split(".");
  return (
    parts.length === 4 &&
    parts.every((part) => /^\d{1,3}$/.test(part) && Number(part) <= 255)
  );
};

const validIpv6 = (value: string): boolean => {
  if (value === "" || value.split("::").length > 2) return false;
  const compressed = value.includes("::");
  const sides = value.split("::");
  const parts = sides.flatMap((side) => (side === "" ? [] : side.split(":")));
  let groupCount = parts.length;
  if (parts.some((part) => part === "")) return false;
  if (parts.at(-1)?.includes(".")) {
    if (!validIpv4(parts.at(-1) ?? "")) return false;
    groupCount += 1;
    parts.pop();
  }
  if (!parts.every((part) => /^[0-9a-f]{1,4}$/i.test(part))) return false;
  return compressed ? groupCount < 8 : groupCount === 8;
};

const validHostname = (value: string): boolean => {
  const hostname = value.endsWith(".") ? value.slice(0, -1) : value;
  return (
    value.length <= 253 &&
    hostname !== "" &&
    hostname.split(".").every(
      (label) =>
        label.length <= 63 &&
        /^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$/i.test(label),
    )
  );
};

const validServerAddress = (value: string): boolean => {
  if (/\s/.test(value) || value === "") return false;
  const bracketed = value.match(/^\[([0-9a-f:.]+)\](?::(\d+))?$/i);
  if (bracketed) return validIpv6(bracketed[1]) && validPort(bracketed[2]);
  // An unbracketed IPv6 literal is accepted only without a port.
  if (value.includes(":") && value.split(":").length > 2) {
    return validIpv6(value);
  }
  const host = value.match(/^([^:]+)(?::(\d+))?$/);
  return host !== null && validHostname(host[1]) && validPort(host[2]);
};

export const validateAdvancedSettings = (
  draft: AdvancedSettings,
): Effect.Effect<FieldErrors> =>
  Effect.sync(() => {
    const errors: FieldErrors = {};
    errors.executable_override = absolutePathError(
      draft.executable_override,
      "Executable override",
    );
    errors.profiles_directory_override = absolutePathError(
      draft.profiles_directory_override,
      "Profiles directory override",
    );
    if (draft.remote_enabled && !validServerAddress(draft.server_address)) {
      errors.server_address =
        draft.server_address === ""
          ? "Server address is required in remote mode."
          : "Enter a hostname or IP address with an optional port from 1 to 65535.";
    }
    return Object.fromEntries(
      Object.entries(errors).filter((entry) => entry[1] !== undefined),
    ) as FieldErrors;
  });
