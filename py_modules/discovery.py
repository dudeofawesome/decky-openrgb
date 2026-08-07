"""Profile path resolution and immediate-child OpenRGB discovery."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from .models import ProfileSummary


SYSTEM_PROFILES_DIRECTORY = Path("/var/lib/OpenRGB")


@dataclass(frozen=True, slots=True)
class DiscoveryResult:
    profiles: tuple[ProfileSummary, ...]
    error: str | None = None
    successful: bool = True


def resolve_profiles_directory(deck_user_home: str | Path, override: str) -> Path:
    """Resolve the configured path without consulting the process user."""

    if override:
        return Path(override)
    return Path(deck_user_home) / ".config" / "OpenRGB"


def discover_profiles(
    configured_directory: str | Path,
    system_directory: str | Path = SYSTEM_PROFILES_DIRECTORY,
) -> DiscoveryResult:
    """Discover exact profile filenames in the two specified directories."""

    configured = Path(configured_directory)
    system = Path(system_directory)

    try:
        configured_entries = _scan_directory(configured)
    except (OSError, ValueError):
        return DiscoveryResult(
            (),
            f"Profiles directory is unavailable: {configured}",
            successful=False,
        )

    entries = configured_entries
    if not _same_path(configured, system):
        try:
            entries.extend(_scan_directory(system))
        except (OSError, ValueError):
            # The system directory is an additional source and commonly does not
            # exist. Its absence must not make a valid configured path unusable.
            pass

    identifiers = set(entries)
    profiles = tuple(
        ProfileSummary(identifier, identifier[:-4])
        for identifier in sorted(
            identifiers,
            key=lambda value: (value[:-4].casefold(), value),
        )
    )
    return DiscoveryResult(profiles)


def _scan_directory(directory: Path) -> list[str]:
    if not directory.is_dir():
        raise NotADirectoryError(directory)

    identifiers: list[str] = []
    with os.scandir(directory) as entries:
        for entry in entries:
            if entry.is_file() and entry.name.lower().endswith(".orp"):
                identifiers.append(entry.name)
    return identifiers


def _same_path(left: Path, right: Path) -> bool:
    try:
        return left.resolve(strict=False) == right.resolve(strict=False)
    except OSError:
        return os.path.abspath(left) == os.path.abspath(right)
