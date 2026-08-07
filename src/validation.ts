import { Effect, ParseResult, Schema } from "effect";

const portPattern = /^\d+$/;
const hostnameLabelPattern = /^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$/i;
const ipv4PartPattern = /^\d{1,3}$/;
const ipv6PartPattern = /^[0-9a-f]{1,4}$/i;

const PortSchema = Schema.String.pipe(
  Schema.filter(
    (value) =>
      portPattern.test(value) && Number(value) >= 1 && Number(value) <= 65535,
  ),
);

const HostnameSchema = Schema.String.pipe(
  Schema.filter((value) => {
    const hostname = value.endsWith(".") ? value.slice(0, -1) : value;
    return (
      value.length <= 253 &&
      hostname !== "" &&
      hostname
        .split(".")
        .every(
          (label) => label.length <= 63 && hostnameLabelPattern.test(label),
        )
    );
  }),
);

const Ipv4Schema = Schema.String.pipe(
  Schema.filter((value) => {
    const parts = value.split(".");
    return (
      parts.length === 4 &&
      parts.every(
        (part) => ipv4PartPattern.test(part) && Number(part) <= 255,
      )
    );
  }),
);

const Ipv6Schema = Schema.String.pipe(
  Schema.filter((value) => {
    if (value === "" || value.split("::").length > 2) return false;

    const compressed = value.includes("::");
    const parts = value
      .split("::")
      .flatMap((side) => (side === "" ? [] : side.split(":")));
    let groupCount = parts.length;

    if (parts.some((part) => part === "")) return false;
    if (parts.at(-1)?.includes(".")) {
      if (!Schema.is(Ipv4Schema)(parts.at(-1))) return false;
      groupCount += 1;
      parts.pop();
    }

    if (!parts.every((part) => ipv6PartPattern.test(part))) return false;
    return compressed ? groupCount < 8 : groupCount === 8;
  }),
);

export const AbsolutePathOverrideSchema = Schema.String.pipe(
  Schema.filter((value) => value === "" || value.startsWith("/")),
);

export const ServerAddressSchema = Schema.String.pipe(
  Schema.filter((value) => {
    if (/\s/.test(value) || value === "") return false;

    const bracketed = value.match(/^\[([0-9a-f:.]+)\](?::(\d+))?$/i);
    if (bracketed) {
      return (
        Schema.is(Ipv6Schema)(bracketed[1]) &&
        (bracketed[2] === undefined || Schema.is(PortSchema)(bracketed[2]))
      );
    }

    if (value.includes(":") && value.split(":").length > 2) {
      return Schema.is(Ipv6Schema)(value);
    }

    const host = value.match(/^([^:]+)(?::(\d+))?$/);
    return (
      host !== null &&
      Schema.is(HostnameSchema)(host[1]) &&
      (host[2] === undefined || Schema.is(PortSchema)(host[2]))
    );
  }),
);

const settingsFields = {
  executable_override: Schema.String,
  profiles_directory_override: Schema.String,
  remote_enabled: Schema.Boolean,
  server_address: Schema.String,
} as const;

export const AdvancedSettingsSchema = Schema.Struct(settingsFields).pipe(
  Schema.filter((draft) => {
    const issues: Array<Schema.FilterIssue> = [];

    if (!Schema.is(AbsolutePathOverrideSchema)(draft.executable_override)) {
      issues.push({
        path: ["executable_override"],
        message: "Executable override must be an absolute path.",
      });
    }
    if (
      !Schema.is(AbsolutePathOverrideSchema)(draft.profiles_directory_override)
    ) {
      issues.push({
        path: ["profiles_directory_override"],
        message: "Profiles directory override must be an absolute path.",
      });
    }
    if (
      draft.remote_enabled &&
      !Schema.is(ServerAddressSchema)(draft.server_address)
    ) {
      issues.push({
        path: ["server_address"],
        message:
          draft.server_address === ""
            ? "Server address is required in remote mode."
            : "Enter a hostname or IP address with an optional port from 1 to 65535.",
      });
    }

    return issues.length === 0 ? undefined : issues;
  }),
);

export type AdvancedSettings = Schema.Schema.Type<typeof AdvancedSettingsSchema>;

export const FieldErrorsSchema = Schema.Struct({
  executable_override: Schema.optional(Schema.String),
  profiles_directory_override: Schema.optional(Schema.String),
  server_address: Schema.optional(Schema.String),
});

export type FieldErrors = Schema.Schema.Type<typeof FieldErrorsSchema>;

const issuesToFieldErrors = (
  issues: ReadonlyArray<ParseResult.ArrayFormatterIssue>,
): FieldErrors =>
  Object.fromEntries(
    issues.flatMap((issue) => {
      const field = issue.path[0];
      return typeof field === "string" ? [[field, issue.message]] : [];
    }),
  );

export const validateAdvancedSettings = (
  draft: AdvancedSettings,
): Effect.Effect<FieldErrors> =>
  Schema.decodeUnknown(AdvancedSettingsSchema, { errors: "all" })(draft).pipe(
    Effect.as({}),
    Effect.catchAll((error) =>
      ParseResult.ArrayFormatter.formatError(error).pipe(
        Effect.map(issuesToFieldErrors),
      ),
    ),
  );
