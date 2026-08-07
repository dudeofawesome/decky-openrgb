import { callable, toaster } from "@decky/api";
import { Effect } from "effect";

import { AdvancedSettings } from "./validation";

export type { AdvancedSettings, FieldErrors } from "./validation";
export { validateAdvancedSettings } from "./validation";

export type ApplyTrigger = "manual" | "startup" | "resume";

export interface Settings {
  selected_profile: string | null;
  automatic_apply: boolean;
  executable_override: string;
  profiles_directory_override: string;
  remote_enabled: boolean;
  server_address: string;
}

export interface Profile {
  identifier: string;
  display_name: string;
}

export interface ApplyResult {
  success: boolean;
  profile: string;
  trigger: ApplyTrigger;
  timestamp: string;
  message: string;
}

export interface LastApplied {
  profile: string;
  timestamp: string;
}

export interface PluginState {
  settings: Settings;
  resolved_executable: string;
  resolved_profiles_directory: string;
  profiles: Profile[];
  discovery_error: string | null;
  settings_error: string | null;
  last_result: ApplyResult | null;
  last_applied: LastApplied | null;
}

export interface ViewState {
  state: PluginState | null;
  busy: "loading" | "refreshing" | "applying" | "updating" | "saving" | null;
  operationError: string | null;
}

const getState = callable<[], PluginState>("get_state");
const refreshProfiles = callable<[], PluginState>("refresh_profiles");
const setSelectedProfile = callable<[identifier: string | null], PluginState>(
  "set_selected_profile",
);
const setAutomaticApply = callable<[enabled: boolean], PluginState>(
  "set_automatic_apply",
);
const saveAdvancedSettings = callable<[draft: AdvancedSettings], PluginState>(
  "save_advanced_settings",
);
const applySelected = callable<[trigger: "manual" | "resume"], ApplyResult>(
  "apply_selected",
);

const errorMessage = (error: unknown): string => {
  if (error instanceof Error && error.message) return error.message;
  if (typeof error === "string") return error;
  if (typeof error === "object" && error !== null) {
    const value = error as { message?: unknown; error?: unknown };
    if (typeof value.message === "string") return value.message;
    if (typeof value.error === "string") return value.error;
  }
  return "The backend request failed.";
};

const backend = <A>(request: () => Promise<A>) =>
  Effect.tryPromise({ try: request, catch: errorMessage });

class OpenRgbController {
  private snapshot: ViewState = {
    state: null,
    busy: "loading",
    operationError: null,
  };

  private readonly listeners = new Set<() => void>();
  private startupWatch: AbortController | null = null;
  private resumeRequest: Promise<void> | null = null;

  getSnapshot = (): ViewState => this.snapshot;

  subscribe = (listener: () => void): (() => void) => {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  };

  private publish(patch: Partial<ViewState>): void {
    this.snapshot = { ...this.snapshot, ...patch };
    this.listeners.forEach((listener) => listener());
  }

  private runStateRequest(
    busy: Exclude<ViewState["busy"], "applying" | null>,
    request: () => Promise<PluginState>,
    notifyStartupFailure = false,
  ): Promise<void> {
    this.publish({ busy, operationError: null });
    return Effect.runPromise(
      backend(request).pipe(
        Effect.tap((state) =>
          Effect.sync(() => {
            this.publish({ state });
            if (
              notifyStartupFailure &&
              state.last_result?.trigger === "startup" &&
              !state.last_result.success
            ) {
              toaster.toast({
                title: "OpenRGB profile failed",
                body: state.last_result.message,
              });
            }
            if (notifyStartupFailure) this.startStartupWatcher(state);
          }),
        ),
        Effect.catchAll((message) =>
          Effect.sync(() => this.publish({ operationError: message })),
        ),
        Effect.ensuring(Effect.sync(() => this.publish({ busy: null }))),
        Effect.asVoid,
      ),
    );
  }

  initialize = (): Promise<void> =>
    this.runStateRequest("loading", getState, true);

  private startStartupWatcher(initial: PluginState): void {
    if (
      !initial.settings.automatic_apply ||
      initial.settings.selected_profile === null ||
      !initial.profiles.some(
        (profile) => profile.identifier === initial.settings.selected_profile,
      ) ||
      initial.last_result?.trigger === "startup"
    ) {
      return;
    }

    this.startupWatch?.abort();
    const abort = new AbortController();
    this.startupWatch = abort;
    const poll = (remaining: number): Effect.Effect<void> => {
      if (remaining === 0) return Effect.void;
      return Effect.sleep("5 seconds").pipe(
        Effect.andThen(backend(getState)),
        Effect.flatMap((state) =>
          Effect.sync(() => this.publish({ state })).pipe(
            Effect.andThen(
              state.last_result?.trigger === "startup" ||
                !state.settings.automatic_apply
                ? Effect.sync(() => {
                    if (state.last_result?.trigger === "startup" && !state.last_result.success) {
                      toaster.toast({
                        title: "OpenRGB profile failed",
                        body: state.last_result.message,
                      });
                    }
                    this.startupWatch = null;
                  })
                : poll(remaining - 1),
            ),
          ),
        ),
        Effect.catchAll(() => poll(remaining - 1)),
      );
    };
    // Four 30-second attempts plus retry intervals can take up to 135 seconds.
    void Effect.runPromise(poll(30), { signal: abort.signal }).catch(() => undefined);
  }

  refresh = (): Promise<void> =>
    this.runStateRequest("refreshing", refreshProfiles);

  select = (identifier: string | null): Promise<void> =>
    this.runStateRequest("updating", () => setSelectedProfile(identifier));

  setAutomatic = (enabled: boolean): Promise<void> =>
    this.runStateRequest("updating", () => setAutomaticApply(enabled));

  save = (draft: AdvancedSettings): Promise<void> =>
    this.runStateRequest("saving", () => saveAdvancedSettings(draft));

  private apply(trigger: "manual" | "resume"): Promise<void> {
    this.publish({ busy: "applying", operationError: null });
    return Effect.runPromise(
      backend(() => applySelected(trigger)).pipe(
        Effect.tap((result) =>
          Effect.sync(() => {
            const state = this.snapshot.state;
            if (state) {
              this.publish({
                state: {
                  ...state,
                  last_result: result,
                  last_applied: result.success
                    ? { profile: result.profile, timestamp: result.timestamp }
                    : state.last_applied,
                },
              });
            }
            if (!result.success) {
              toaster.toast({ title: "OpenRGB profile failed", body: result.message });
            }
          }),
        ),
        Effect.catchAll((message) =>
          Effect.sync(() => this.publish({ operationError: message })),
        ),
        Effect.ensuring(Effect.sync(() => this.publish({ busy: null }))),
        Effect.asVoid,
      ),
    );
  }

  applyManual = (): Promise<void> => this.apply("manual");

  resume = (): Promise<void> => {
    if (!this.snapshot.state?.settings.automatic_apply) return Promise.resolve();
    if (this.resumeRequest) return this.resumeRequest;
    const request = this.apply("resume").finally(() => {
      if (this.resumeRequest === request) this.resumeRequest = null;
    });
    this.resumeRequest = request;
    return request;
  };

  shutdown = (): void => {
    this.startupWatch?.abort();
    this.startupWatch = null;
  };
}

export const controller = new OpenRgbController();
