from __future__ import annotations

import unittest

from py_modules.models import (
    ApplyResult,
    ApplyTrigger,
    LastApplied,
    PersistedSettings,
    PluginState,
    ProfileSummary,
)


class ModelTests(unittest.TestCase):

    def test_defaults_match_specification(self) -> None:
        self.assertEqual(
            PersistedSettings().to_dict(),
            {
                "selected_profile": None,
                "automatic_apply": False,
                "executable_override": "",
                "profiles_directory_override": "",
                "remote_enabled": False,
                "server_address": "",
            },
        )

    def test_plugin_state_is_frontend_serializable(self) -> None:
        state = PluginState(
            settings=PersistedSettings(selected_profile="Sunset.orp"),
            resolved_profiles_directory="/home/deck/.config/OpenRGB",
            profiles=(ProfileSummary("Sunset.orp", "Sunset"), ),
            last_result=ApplyResult(
                True,
                "Sunset.orp",
                ApplyTrigger.MANUAL,
                "2026-08-05T12:00:00Z",
                "Profile applied.",
            ),
            last_applied=LastApplied("Sunset.orp", "2026-08-05T12:00:00Z"),
        )

        value = state.to_dict()

        self.assertEqual(value["profiles"][0]["identifier"], "Sunset.orp")
        self.assertEqual(value["last_result"]["trigger"], "manual")
        self.assertEqual(value["last_applied"]["profile"], "Sunset.orp")


if __name__ == "__main__":
    unittest.main()
