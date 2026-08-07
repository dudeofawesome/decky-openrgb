from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from py_modules.discovery import discover_profiles, resolve_profiles_directory


class DiscoveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)
        self.configured = self.root / "configured"
        self.system = self.root / "system"
        self.configured.mkdir()
        self.system.mkdir()

    def test_filters_immediate_files_and_sorts_exact_identifiers(self) -> None:
        for name in ("zebra.orp", "Alpha.ORP", "beta.orp", "ignore.txt"):
            (self.configured / name).write_text("profile", encoding="utf-8")
        (self.configured / "folder.orp").mkdir()
        nested = self.configured / "nested"
        nested.mkdir()
        (nested / "Nested.orp").write_text("profile", encoding="utf-8")
        (self.system / "System.OrP").write_text("profile", encoding="utf-8")

        result = discover_profiles(self.configured, self.system)

        self.assertIsNone(result.error)
        self.assertEqual(
            [(item.identifier, item.display_name) for item in result.profiles],
            [
                ("Alpha.ORP", "Alpha"),
                ("beta.orp", "beta"),
                ("System.OrP", "System"),
                ("zebra.orp", "zebra"),
            ],
        )

    def test_same_path_is_scanned_once_and_duplicate_names_are_deduped(self) -> None:
        (self.configured / "Only.orp").write_text("profile", encoding="utf-8")
        with patch("py_modules.discovery._scan_directory", wraps=None) as scan:
            scan.return_value = ["Only.orp"]
            result = discover_profiles(self.configured, self.configured)

        scan.assert_called_once_with(self.configured)
        self.assertEqual([item.identifier for item in result.profiles], ["Only.orp"])

    def test_case_insensitive_ties_use_exact_identifier(self) -> None:
        with patch(
            "py_modules.discovery._scan_directory",
            side_effect=[["alpha.orp", "Alpha.ORP"], []],
        ):
            result = discover_profiles(self.configured, self.system)

        self.assertEqual(
            [item.identifier for item in result.profiles],
            ["Alpha.ORP", "alpha.orp"],
        )

    def test_invalid_configured_path_is_an_empty_error(self) -> None:
        result = discover_profiles(self.root / "missing", self.system)

        self.assertFalse(result.successful)
        self.assertEqual(result.profiles, ())
        self.assertIn("Profiles directory is unavailable", result.error or "")

        nul_result = discover_profiles("/invalid\0path", self.system)
        self.assertFalse(nul_result.successful)
        self.assertEqual(nul_result.profiles, ())

    def test_readable_empty_directory_is_successful(self) -> None:
        result = discover_profiles(self.configured, self.system)

        self.assertTrue(result.successful)
        self.assertEqual(result.profiles, ())
        self.assertIsNone(result.error)

    def test_system_directory_absence_does_not_fail_valid_configured_path(self) -> None:
        result = discover_profiles(self.configured, self.root / "missing")

        self.assertTrue(result.successful)
        self.assertIsNone(result.error)

    def test_default_resolution_uses_decky_home(self) -> None:
        self.assertEqual(
            resolve_profiles_directory("/home/deck", ""),
            Path("/home/deck/.config/OpenRGB"),
        )
        self.assertEqual(
            resolve_profiles_directory("/home/deck", "/profiles"),
            Path("/profiles"),
        )


if __name__ == "__main__":
    unittest.main()
