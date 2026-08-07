from __future__ import annotations

import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


class EntrypointTests(unittest.TestCase):
    def test_file_loaded_entrypoint_resolves_sibling_backend_package(self) -> None:
        plugin_root = Path(__file__).resolve().parents[1]

        with tempfile.TemporaryDirectory() as temporary_directory:
            loader_root = Path(temporary_directory)
            (loader_root / "decky.py").write_text("", encoding="utf-8")
            script = textwrap.dedent(
                f"""
                import importlib.util
                import sys

                plugin_root = {str(plugin_root)!r}
                assert plugin_root not in sys.path
                spec = importlib.util.spec_from_file_location(
                    "decky_openrgb_main",
                    plugin_root + "/main.py",
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                assert module.Plugin
                """
            )

            result = subprocess.run(
                [sys.executable, "-c", script],
                cwd=loader_root,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
