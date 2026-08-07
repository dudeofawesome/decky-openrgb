"""Safe JSON persistence for plugin settings."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile

from .models import PersistedSettings


class SettingsPersistenceError(RuntimeError):
    """A settings update could not be committed to disk."""


@dataclass(frozen=True, slots=True)
class SettingsLoadResult:
    settings: PersistedSettings
    error: str | None = None


class SettingsStore:
    """Load settings safely and replace the complete document atomically."""

    def __init__(self, path: str | Path, logger: logging.Logger | None = None):
        self.path = Path(path)
        self.logger = logger or logging.getLogger(__name__)

    def load(self) -> SettingsLoadResult:
        if not self.path.exists():
            return SettingsLoadResult(PersistedSettings())

        try:
            with self.path.open("r", encoding="utf-8") as settings_file:
                raw_settings = json.load(settings_file)
            settings = PersistedSettings.from_mapping(raw_settings)
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
            message = "Saved settings could not be loaded; defaults are in use."
            self.logger.error("Failed to load settings from %s: %s", self.path, error)
            return SettingsLoadResult(PersistedSettings(), message)

        return SettingsLoadResult(settings)

    def save(self, settings: PersistedSettings) -> None:
        """Commit one complete settings document with a same-directory rename."""

        temporary_path: Path | None = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with NamedTemporaryFile(
                "w",
                encoding="utf-8",
                dir=self.path.parent,
                prefix=f".{self.path.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary_file:
                temporary_path = Path(temporary_file.name)
                json.dump(settings.to_dict(), temporary_file, indent=2, sort_keys=True)
                temporary_file.write("\n")
                temporary_file.flush()
                os.fsync(temporary_file.fileno())

            os.replace(temporary_path, self.path)
            temporary_path = None
            try:
                self._sync_parent_directory()
            except OSError as error:
                # The atomic replacement is already committed. Reporting the
                # save as failed here would leave runtime and disk state split.
                self.logger.warning(
                    "Settings were saved but the parent directory could not "
                    "be synchronized: %s",
                    error,
                )
        except OSError as error:
            self.logger.error("Failed to persist settings to %s: %s", self.path, error)
            raise SettingsPersistenceError("Settings could not be saved.") from error
        finally:
            if temporary_path is not None:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError:
                    self.logger.warning(
                        "Failed to remove temporary settings file %s", temporary_path
                    )

    def _sync_parent_directory(self) -> None:
        directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        try:
            directory_fd = os.open(self.path.parent, directory_flags)
        except OSError:
            return
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
