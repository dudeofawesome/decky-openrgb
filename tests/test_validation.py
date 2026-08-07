from __future__ import annotations

import unittest

from py_modules.validation import (
    AdvancedSettingsValidationError,
    validate_advanced_settings,
)


def draft(**changes: object) -> dict[str, object]:
    value: dict[str, object] = {
        "executable_override": "",
        "profiles_directory_override": "",
        "remote_enabled": False,
        "server_address": "",
    }
    value.update(changes)
    return value


class AdvancedValidationTests(unittest.TestCase):
    def test_empty_local_settings_are_valid(self) -> None:
        self.assertEqual(validate_advanced_settings(draft()), draft())

    def test_paths_must_be_absolute_but_need_not_exist(self) -> None:
        validated = validate_advanced_settings(
            draft(
                executable_override="/removable/OpenRGB",
                profiles_directory_override="/missing/profiles",
            )
        )
        self.assertEqual(validated["executable_override"], "/removable/OpenRGB")

        with self.assertRaises(AdvancedSettingsValidationError) as context:
            validate_advanced_settings(
                draft(executable_override="bin/OpenRGB", profiles_directory_override="profiles")
            )
        self.assertEqual(
            set(context.exception.field_errors),
            {"executable_override", "profiles_directory_override"},
        )

    def test_remote_address_forms_and_ports(self) -> None:
        for address in (
            "openrgb.local",
            "openrgb.local:6742",
            "192.168.1.2",
            "192.168.1.2:1",
            "[2001:db8::1]",
            "[2001:db8::1]:65535",
            "2001:db8::1",
        ):
            with self.subTest(address=address):
                validate_advanced_settings(
                    draft(remote_enabled=True, server_address=address)
                )

        for address in ("", "host name", "host:0", "host:65536", "[bad]:42"):
            with self.subTest(address=address):
                with self.assertRaises(AdvancedSettingsValidationError):
                    validate_advanced_settings(
                        draft(remote_enabled=True, server_address=address)
                    )

    def test_disabled_remote_address_is_not_used_or_validated(self) -> None:
        validated = validate_advanced_settings(
            draft(remote_enabled=False, server_address="draft with whitespace")
        )
        self.assertEqual(validated["server_address"], "draft with whitespace")


if __name__ == "__main__":
    unittest.main()
