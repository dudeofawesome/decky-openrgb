from __future__ import annotations

import asyncio
import logging
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from unittest.mock import patch

from py_modules.backend import OpenRGBBackend
from py_modules.models import PersistedSettings
from py_modules.settings import SettingsStore
from py_modules.validation import AdvancedSettingsValidationError


class FakeProcess:
    def __init__(
        self,
        returncode: int = 0,
        stdout: bytes = b"Profile loaded successfully\n",
        stderr: bytes = b"",
    ):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.terminated = False
        self.killed = False

    async def communicate(self) -> tuple[bytes, bytes]:
        return self.stdout, self.stderr

    def terminate(self) -> None:
        self.terminated = True

    def kill(self) -> None:
        self.killed = True


class HangingProcess(FakeProcess):
    def __init__(self) -> None:
        super().__init__()
        self.calls = 0

    async def communicate(self) -> tuple[bytes, bytes]:
        self.calls += 1
        if self.calls == 1:
            await asyncio.Event().wait()
        return b"partial output", b"timeout detail"


class GatedProcess(FakeProcess):
    def __init__(self, started: asyncio.Event, release: asyncio.Event) -> None:
        super().__init__()
        self.started = started
        self.release = release

    async def communicate(self) -> tuple[bytes, bytes]:
        self.started.set()
        await self.release.wait()
        return await super().communicate()


class StubbornProcess(FakeProcess):
    def __init__(self, started: asyncio.Event) -> None:
        super().__init__()
        self.started = started
        self.stopped = asyncio.Event()

    async def communicate(self) -> tuple[bytes, bytes]:
        self.started.set()
        await self.stopped.wait()
        return b"stopped output", b"stopped detail"

    def kill(self) -> None:
        super().kill()
        self.stopped.set()


class ProcessFactory:
    def __init__(self, processes: list[FakeProcess] | None = None):
        self.processes = list(processes or [FakeProcess()])
        self.calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = []
        self.active = 0
        self.max_active = 0

    async def __call__(self, *arguments: Any, **keywords: Any) -> FakeProcess:
        self.calls.append((arguments, keywords))
        process = self.processes.pop(0)
        original_communicate = process.communicate

        async def tracked_communicate() -> tuple[bytes, bytes]:
            self.active += 1
            self.max_active = max(self.max_active, self.active)
            try:
                return await original_communicate()
            finally:
                self.active -= 1

        process.communicate = tracked_communicate  # type: ignore[method-assign]
        return process


class BackendTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)
        self.home = self.root / "home"
        self.profiles = self.home / ".config" / "OpenRGB"
        self.profiles.mkdir(parents=True)
        self.system = self.root / "system"
        self.system.mkdir()
        self.settings_path = self.root / "settings" / "settings.json"
        self.store = SettingsStore(self.settings_path)

    def make_backend(
        self,
        factory: ProcessFactory | Any | None = None,
        *,
        sleep: Any = asyncio.sleep,
    ) -> OpenRGBBackend:
        return OpenRGBBackend(
            self.store,
            self.home,
            logging.getLogger("backend-test"),
            system_profiles_directory=self.system,
            process_factory=factory or ProcessFactory(),
            sleep=sleep,
            clock=lambda: datetime(2026, 8, 5, 12, 0, tzinfo=timezone.utc),
        )

    async def select(self, backend: OpenRGBBackend, name: str = "My Profile.orp") -> None:
        (self.profiles / name).write_text("profile", encoding="utf-8")
        await backend.refresh_profiles()
        await backend.set_selected_profile(name)

    async def test_start_state_refresh_and_selection_reconciliation(self) -> None:
        (self.system / "System.ORP").write_text("profile", encoding="utf-8")
        self.store.save(
            PersistedSettings(selected_profile="Gone.orp", automatic_apply=True)
        )
        backend = self.make_backend()

        await backend.start()
        state = await backend.get_state()

        self.assertEqual(state["settings"]["selected_profile"], None)
        self.assertFalse(state["settings"]["automatic_apply"])
        self.assertEqual(state["profiles"][0]["identifier"], "System.ORP")
        self.assertEqual(self.store.load().settings, PersistedSettings())
        self.assertEqual(state["resolved_executable"], "openrgb")
        self.assertEqual(
            state["resolved_profiles_directory"], str(self.profiles)
        )

    async def test_selection_persists_without_launching_and_automation_precondition(self) -> None:
        factory = ProcessFactory()
        backend = self.make_backend(factory)
        await backend.start()
        await self.select(backend)

        self.assertEqual(factory.calls, [])
        self.assertEqual(
            self.store.load().settings.selected_profile, "My Profile.orp"
        )
        await backend.set_automatic_apply(True)
        await backend.set_selected_profile(None)
        self.assertFalse(self.store.load().settings.automatic_apply)
        with self.assertRaisesRegex(ValueError, "Choose an available"):
            await backend.set_automatic_apply(True)

    async def test_advanced_save_is_atomic_and_rescans(self) -> None:
        backend = self.make_backend()
        await backend.start()
        await self.select(backend)
        previous = self.store.load().settings

        with self.assertRaises(AdvancedSettingsValidationError):
            await backend.save_advanced_settings(
                {
                    "executable_override": "relative",
                    "profiles_directory_override": "relative",
                    "remote_enabled": True,
                    "server_address": "bad address",
                }
            )
        self.assertEqual(self.store.load().settings, previous)

        new_profiles = self.root / "new profiles"
        new_profiles.mkdir()
        state = await backend.save_advanced_settings(
            {
                "executable_override": "/opt/Open RGB/OpenRGB",
                "profiles_directory_override": str(new_profiles),
                "remote_enabled": True,
                "server_address": "server.local:6742",
            }
        )
        self.assertEqual(state["profiles"], [])
        self.assertIsNone(state["settings"]["selected_profile"])
        self.assertEqual(
            self.store.load().settings.executable_override,
            "/opt/Open RGB/OpenRGB",
        )

    async def test_exact_local_and_remote_argument_vectors_are_literal(self) -> None:
        local_factory = ProcessFactory()
        backend = self.make_backend(local_factory)
        await backend.start()
        name = "$(touch nope); My Profile.orp"
        await self.select(backend, name)
        result = await backend.apply_selected("manual")

        self.assertTrue(result["success"])
        self.assertEqual(
            local_factory.calls[0][0],
            (
                "openrgb",
                "--config",
                str(self.profiles),
                "--profile",
                name,
            ),
        )

        remote_factory = ProcessFactory()
        backend._process_factory = remote_factory
        await backend.save_advanced_settings(
            {
                "executable_override": "/opt/Open RGB/OpenRGB",
                "profiles_directory_override": "",
                "remote_enabled": True,
                "server_address": "server.local:6742",
            }
        )
        await backend.set_selected_profile(name)
        await backend.apply_selected("manual")
        self.assertEqual(
            remote_factory.calls[0][0],
            (
                "/opt/Open RGB/OpenRGB",
                "--client",
                "server.local:6742",
                "--config",
                str(self.profiles),
                "--profile",
                name,
            ),
        )
        self.assertNotIn("shell", remote_factory.calls[0][1])

    async def test_application_result_cases_and_history(self) -> None:
        processes = [
            FakeProcess(),
            FakeProcess(returncode=2, stderr=b"failure detail"),
            FakeProcess(stdout=b"ordinary output"),
        ]
        factory = ProcessFactory(processes)
        backend = self.make_backend(factory)
        await backend.start()
        await self.select(backend)

        success = await backend.apply_selected("manual")
        exit_failure = await backend.apply_selected("manual")
        marker_failure = await backend.apply_selected("manual")
        state = await backend.get_state()

        self.assertTrue(success["success"])
        self.assertFalse(exit_failure["success"])
        self.assertIn("status 2", exit_failure["message"])
        self.assertFalse(marker_failure["success"])
        self.assertEqual(state["last_result"], marker_failure)
        self.assertEqual(state["last_applied"]["profile"], "My Profile.orp")
        self.assertEqual(state["last_applied"]["timestamp"], success["timestamp"])

    async def test_launch_error_and_timeout_are_failures_and_terminate(self) -> None:
        async def launch_error(*args: Any, **kwargs: Any) -> FakeProcess:
            raise FileNotFoundError("missing")

        backend = self.make_backend(launch_error)
        await backend.start()
        await self.select(backend)
        result = await backend.apply_selected("manual")
        self.assertFalse(result["success"])
        self.assertIn("started", result["message"])

        hanging = HangingProcess()
        backend._process_factory = ProcessFactory([hanging])
        with self.assertLogs("backend-test", level="ERROR") as logs:
            with patch("py_modules.backend.PROCESS_TIMEOUT_SECONDS", 0.001):
                result = await backend.apply_selected("manual")
        self.assertFalse(result["success"])
        self.assertTrue(hanging.terminated)
        self.assertIn("partial output", "\n".join(logs.output))
        self.assertIn("timeout detail", "\n".join(logs.output))

        async def invalid_arguments(*args: Any, **kwargs: Any) -> FakeProcess:
            raise ValueError("embedded null byte")

        backend._process_factory = invalid_arguments
        result = await backend.apply_selected("manual")
        self.assertFalse(result["success"])
        self.assertIn("started", result["message"])

    async def test_empty_or_stale_selection_rejects_without_process(self) -> None:
        factory = ProcessFactory()
        backend = self.make_backend(factory)
        await backend.start()
        empty = await backend.apply_selected("manual")
        self.assertFalse(empty["success"])
        await self.select(backend)
        (self.profiles / "My Profile.orp").unlink()
        await backend.refresh_profiles()
        stale = await backend.apply_selected("manual")
        self.assertFalse(stale["success"])
        self.assertEqual(factory.calls, [])

    async def test_automatic_disabled_retry_exhaustion_and_early_success(self) -> None:
        sleep_calls: list[float] = []

        async def no_wait(delay: float) -> None:
            sleep_calls.append(delay)

        factory = ProcessFactory([FakeProcess()] * 4)
        backend = self.make_backend(factory, sleep=no_wait)
        await backend.start()
        await self.select(backend)
        disabled = await backend.apply_selected("resume")
        self.assertFalse(disabled["success"])
        self.assertEqual(factory.calls, [])

        await backend.set_automatic_apply(True)
        factory.processes = [FakeProcess(returncode=1) for _ in range(4)]
        final = await backend.apply_selected("resume")
        self.assertFalse(final["success"])
        self.assertEqual(len(factory.calls), 4)
        self.assertEqual(sleep_calls, [5.0, 5.0, 5.0])

        factory.calls.clear()
        sleep_calls.clear()
        factory.processes = [FakeProcess(returncode=1), FakeProcess()]
        final = await backend.apply_selected("resume")
        self.assertTrue(final["success"])
        self.assertEqual(len(factory.calls), 2)
        self.assertEqual(sleep_calls, [5.0])

    async def test_startup_automation_runs_after_discovery(self) -> None:
        (self.profiles / "Startup.orp").write_text("profile", encoding="utf-8")
        self.store.save(
            PersistedSettings(selected_profile="Startup.orp", automatic_apply=True)
        )
        factory = ProcessFactory([FakeProcess()])
        backend = self.make_backend(factory)

        await backend.start()
        result = await backend.wait_for_startup()

        self.assertIsNotNone(result)
        self.assertTrue(result.success)  # type: ignore[union-attr]
        self.assertEqual(result.trigger.value, "startup")  # type: ignore[union-attr]
        self.assertEqual(len(factory.calls), 1)

    async def test_manual_applications_are_serialized_and_unload_blocks_new_work(self) -> None:
        started = asyncio.Event()
        release = asyncio.Event()
        factory = ProcessFactory(
            [GatedProcess(started, release), FakeProcess()]
        )
        backend = self.make_backend(factory)
        await backend.start()
        await self.select(backend)

        first = asyncio.create_task(backend.apply_selected("manual"))
        await started.wait()
        second = asyncio.create_task(backend.apply_selected("manual"))
        await asyncio.sleep(0)
        self.assertEqual(len(factory.calls), 1)
        release.set()
        await asyncio.gather(first, second)
        self.assertEqual(len(factory.calls), 2)
        self.assertEqual(factory.max_active, 1)

        await backend.unload()
        rejected = await backend.apply_selected("manual")
        self.assertFalse(rejected["success"])
        self.assertIn("unloading", rejected["message"])
        self.assertEqual(len(factory.calls), 2)

    async def test_queued_manual_revalidates_selection_before_launch(self) -> None:
        started = asyncio.Event()
        release = asyncio.Event()
        factory = ProcessFactory([GatedProcess(started, release), FakeProcess()])
        backend = self.make_backend(factory)
        await backend.start()
        await self.select(backend)

        first = asyncio.create_task(backend.apply_selected("manual"))
        await started.wait()
        queued = asyncio.create_task(backend.apply_selected("manual"))
        await asyncio.sleep(0)
        await backend.set_selected_profile(None)
        release.set()

        first_result, queued_result = await asyncio.gather(first, queued)
        self.assertTrue(first_result["success"])
        self.assertFalse(queued_result["success"])
        self.assertIn("available profile", queued_result["message"])
        self.assertEqual(len(factory.calls), 1)

    async def test_unload_cancels_running_manual_and_kills_stubborn_child(self) -> None:
        started = asyncio.Event()
        process = StubbornProcess(started)
        factory = ProcessFactory([process])
        backend = self.make_backend(factory)
        await backend.start()
        await self.select(backend)

        application = asyncio.create_task(backend.apply_selected("manual"))
        await started.wait()
        with patch(
            "py_modules.backend.PROCESS_TERMINATE_GRACE_SECONDS", 0.001
        ):
            await backend.unload()

        with self.assertRaises(asyncio.CancelledError):
            await application
        self.assertTrue(process.terminated)
        self.assertTrue(process.killed)
        self.assertEqual(factory.active, 0)

    async def test_resume_coalescing_and_unload_cancels_retry(self) -> None:
        retry_started = asyncio.Event()
        release_retry = asyncio.Event()

        async def controlled_sleep(delay: float) -> None:
            retry_started.set()
            await release_retry.wait()

        factory = ProcessFactory([FakeProcess(returncode=1), FakeProcess()])
        backend = self.make_backend(factory, sleep=controlled_sleep)
        await backend.start()
        await self.select(backend)
        await backend.set_automatic_apply(True)

        first = asyncio.create_task(backend.apply_selected("resume"))
        await retry_started.wait()
        second = asyncio.create_task(backend.apply_selected("resume"))
        release_retry.set()
        first_result, second_result = await asyncio.gather(first, second)
        self.assertEqual(first_result, second_result)
        self.assertEqual(len(factory.calls), 2)

        retry_started.clear()
        release_retry.clear()
        factory.calls.clear()
        factory.processes = [FakeProcess(returncode=1), FakeProcess()]
        pending = asyncio.create_task(backend.apply_selected("resume"))
        await retry_started.wait()
        await backend.unload()
        with self.assertRaises(asyncio.CancelledError):
            await pending
        self.assertEqual(len(factory.calls), 1)

    async def test_automatic_revalidates_selection_between_retries(self) -> None:
        retry_started = asyncio.Event()
        continue_retry = asyncio.Event()

        async def controlled_sleep(delay: float) -> None:
            retry_started.set()
            await continue_retry.wait()

        factory = ProcessFactory([FakeProcess(returncode=1), FakeProcess()])
        backend = self.make_backend(factory, sleep=controlled_sleep)
        await backend.start()
        await self.select(backend)
        await backend.set_automatic_apply(True)

        application = asyncio.create_task(backend.apply_selected("resume"))
        await retry_started.wait()
        await backend.set_selected_profile(None)
        continue_retry.set()
        result = await application

        self.assertFalse(result["success"])
        self.assertIn("disabled", result["message"])
        self.assertEqual(len(factory.calls), 1)
        self.assertEqual((await backend.get_state())["last_result"], result)


if __name__ == "__main__":
    unittest.main()
