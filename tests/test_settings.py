from __future__ import annotations

import json
import logging
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from py_modules.models import PersistedSettings
from py_modules.settings import SettingsPersistenceError, SettingsStore


class SettingsStoreTests(unittest.TestCase):

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.path = Path(
            self.temporary_directory.name) / "nested" / "settings.json"
        self.store = SettingsStore(self.path,
                                   logging.getLogger("settings-test"))

    def test_missing_storage_loads_defaults_without_an_error(self) -> None:
        result = self.store.load()

        self.assertEqual(result.settings, PersistedSettings())
        self.assertIsNone(result.error)

    def test_all_fields_round_trip(self) -> None:
        expected = PersistedSettings(
            selected_profile="My Profile.ORP",
            automatic_apply=True,
            executable_override="/opt/Open RGB/OpenRGB",
            profiles_directory_override="/home/deck/My Profiles",
            remote_enabled=True,
            server_address="openrgb.local:6742",
        )

        self.store.save(expected)
        actual = SettingsStore(self.path).load()

        self.assertEqual(actual.settings, expected)
        self.assertIsNone(actual.error)
        self.assertEqual(list(self.path.parent.glob("*.tmp")), [])

    def test_malformed_json_loads_defaults_and_reports_an_error(self) -> None:
        self.path.parent.mkdir(parents=True)
        self.path.write_text("{not json", encoding="utf-8")

        result = self.store.load()

        self.assertEqual(result.settings, PersistedSettings())
        self.assertEqual(
            result.error,
            "Saved settings could not be loaded; defaults are in use.")

    def test_wrong_field_type_loads_defaults_and_reports_an_error(
            self) -> None:
        self.path.parent.mkdir(parents=True)
        self.path.write_text(json.dumps({"automatic_apply": "yes"}),
                             encoding="utf-8")

        result = self.store.load()

        self.assertEqual(result.settings, PersistedSettings())
        self.assertIsNotNone(result.error)

    def test_save_replaces_the_complete_document(self) -> None:
        self.path.parent.mkdir(parents=True)
        self.path.write_text(json.dumps({"obsolete": True}), encoding="utf-8")

        self.store.save(PersistedSettings(selected_profile="Ocean.orp"))

        stored = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertNotIn("obsolete", stored)
        self.assertEqual(stored["selected_profile"], "Ocean.orp")
        self.assertEqual(set(stored), set(PersistedSettings().to_dict()))

    def test_failed_atomic_replace_preserves_previous_settings(self) -> None:
        self.path.parent.mkdir(parents=True)
        previous = PersistedSettings(selected_profile="Previous.orp")
        self.path.write_text(json.dumps(previous.to_dict()), encoding="utf-8")

        with patch(
                "py_modules.settings.os.replace",
                side_effect=OSError("disk error"),
        ):
            with self.assertRaisesRegex(SettingsPersistenceError,
                                        "Settings could not be saved"):
                self.store.save(PersistedSettings(selected_profile="New.orp"))

        self.assertEqual(self.store.load().settings, previous)
        self.assertEqual(list(self.path.parent.iterdir()), [self.path])

    def test_parent_sync_failure_after_replace_keeps_committed_save(self) -> None:
        expected = PersistedSettings(selected_profile="Committed.orp")

        with patch.object(
            self.store,
            "_sync_parent_directory",
            side_effect=OSError("sync error"),
        ):
            with self.assertLogs("settings-test", level="WARNING"):
                self.store.save(expected)

        self.assertEqual(self.store.load().settings, expected)


if __name__ == "__main__":
    unittest.main()
