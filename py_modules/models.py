"""Typed values shared by the OpenRGB backend operations."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Mapping


DEFAULT_EXECUTABLE = "openrgb"


class ApplyTrigger(str, Enum):
    """The action that requested an OpenRGB application."""

    MANUAL = "manual"
    STARTUP = "startup"
    RESUME = "resume"


@dataclass(frozen=True, slots=True)
class PersistedSettings:
    """All settings which survive a backend restart."""

    selected_profile: str | None = None
    automatic_apply: bool = False
    executable_override: str = ""
    profiles_directory_override: str = ""
    remote_enabled: bool = False
    server_address: str = ""

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> PersistedSettings:
        """Decode storage strictly so corrupt values cannot enter runtime state."""

        if not isinstance(value, Mapping):
            raise ValueError("settings must be a JSON object")

        selected_profile = value.get("selected_profile")
        if selected_profile is not None and not isinstance(selected_profile, str):
            raise ValueError("selected_profile must be a string or null")

        automatic_apply = value.get("automatic_apply", False)
        remote_enabled = value.get("remote_enabled", False)
        if not isinstance(automatic_apply, bool):
            raise ValueError("automatic_apply must be a boolean")
        if not isinstance(remote_enabled, bool):
            raise ValueError("remote_enabled must be a boolean")

        string_fields: dict[str, str] = {}
        for name in (
            "executable_override",
            "profiles_directory_override",
            "server_address",
        ):
            field_value = value.get(name, "")
            if not isinstance(field_value, str):
                raise ValueError(f"{name} must be a string")
            string_fields[name] = field_value

        return cls(
            selected_profile=selected_profile,
            automatic_apply=automatic_apply,
            remote_enabled=remote_enabled,
            **string_fields,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ProfileSummary:
    identifier: str
    display_name: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ApplyResult:
    success: bool
    profile: str
    trigger: ApplyTrigger
    timestamp: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["trigger"] = self.trigger.value
        return value


@dataclass(frozen=True, slots=True)
class LastApplied:
    """Historical record of the last successful action by this plugin."""

    profile: str
    timestamp: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class PluginState:
    settings: PersistedSettings = field(default_factory=PersistedSettings)
    resolved_executable: str = DEFAULT_EXECUTABLE
    resolved_profiles_directory: str = ""
    profiles: tuple[ProfileSummary, ...] = ()
    discovery_error: str | None = None
    settings_error: str | None = None
    last_result: ApplyResult | None = None
    last_applied: LastApplied | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "settings": self.settings.to_dict(),
            "resolved_executable": self.resolved_executable,
            "resolved_profiles_directory": self.resolved_profiles_directory,
            "profiles": [profile.to_dict() for profile in self.profiles],
            "discovery_error": self.discovery_error,
            "settings_error": self.settings_error,
            "last_result": (
                self.last_result.to_dict() if self.last_result is not None else None
            ),
            "last_applied": (
                self.last_applied.to_dict() if self.last_applied is not None else None
            ),
        }
