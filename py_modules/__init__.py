"""Backend domain services for Decky OpenRGB."""

from .backend import OpenRGBBackend
from .discovery import (
    DiscoveryResult,
    discover_profiles,
    resolve_profiles_directory,
)

from .models import (
    ApplyResult,
    ApplyTrigger,
    LastApplied,
    PersistedSettings,
    PluginState,
    ProfileSummary,
)
from .settings import SettingsLoadResult, SettingsPersistenceError, SettingsStore
from .validation import (
    AdvancedSettingsValidationError,
    validate_advanced_settings,
)

__all__ = [
    "AdvancedSettingsValidationError",
    "ApplyResult",
    "ApplyTrigger",
    "DiscoveryResult",
    "LastApplied",
    "OpenRGBBackend",
    "PersistedSettings",
    "PluginState",
    "ProfileSummary",
    "SettingsLoadResult",
    "SettingsPersistenceError",
    "SettingsStore",
    "discover_profiles",
    "resolve_profiles_directory",
    "validate_advanced_settings",
]
