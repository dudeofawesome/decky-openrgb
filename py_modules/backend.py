"""OpenRGB backend service used by Decky's required entrypoint."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .discovery import (
    SYSTEM_PROFILES_DIRECTORY,
    discover_profiles,
    resolve_profiles_directory,
)
from .models import (
    ApplyResult,
    ApplyTrigger,
    LastApplied,
    PersistedSettings,
    PluginState,
)
from .settings import SettingsStore
from .validation import validate_advanced_settings


SUCCESS_MARKER = "Profile loaded successfully"
PROCESS_TIMEOUT_SECONDS = 30.0
PROCESS_TERMINATE_GRACE_SECONDS = 2.0
AUTOMATIC_RETRY_SECONDS = 5.0
AUTOMATIC_ATTEMPTS = 4


class OpenRGBBackend:
    """Own mutable plugin state, child processes, and automation lifecycle."""

    def __init__(
        self,
        settings_store: SettingsStore,
        deck_user_home: str | Path,
        logger: logging.Logger | None = None,
        *,
        system_profiles_directory: str | Path = SYSTEM_PROFILES_DIRECTORY,
        process_factory: Callable[..., Awaitable[Any]] = asyncio.create_subprocess_exec,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
        clock: Callable[[], datetime] | None = None,
    ):
        self._store = settings_store
        self._deck_user_home = Path(deck_user_home)
        self._system_profiles_directory = Path(system_profiles_directory)
        self._logger = logger or logging.getLogger(__name__)
        self._process_factory = process_factory
        self._sleep = sleep
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._state = PluginState()
        self._apply_lock = asyncio.Lock()
        self._startup_task: asyncio.Task[ApplyResult | None] | None = None
        self._resume_task: asyncio.Task[ApplyResult] | None = None
        self._manual_tasks: set[asyncio.Task[Any]] = set()
        self._unloading = False

    async def start(self) -> None:
        loaded = self._store.load()
        self._state = replace(
            self._state,
            settings=loaded.settings,
            settings_error=loaded.error,
        )
        self._scan_profiles()
        if (
            self._state.settings.automatic_apply
            and self._selection_is_available()
        ):
            self._startup_task = asyncio.create_task(
                self._automatic_sequence(ApplyTrigger.STARTUP)
            )

    async def get_state(self) -> dict[str, Any]:
        return self._public_state().to_dict()

    async def refresh_profiles(self) -> dict[str, Any]:
        self._scan_profiles()
        return self._public_state().to_dict()

    async def set_selected_profile(
        self, identifier: str | None
    ) -> dict[str, Any]:
        available = {profile.identifier for profile in self._state.profiles}
        if identifier is not None and identifier not in available:
            raise ValueError("Selected profile is not available.")

        settings = replace(self._state.settings, selected_profile=identifier)
        if identifier is None:
            settings = replace(settings, automatic_apply=False)
        self._store.save(settings)
        self._state = replace(
            self._state, settings=settings, settings_error=None
        )
        return self._public_state().to_dict()

    async def set_automatic_apply(self, enabled: bool) -> dict[str, Any]:
        if not isinstance(enabled, bool):
            raise ValueError("Automatic apply must be true or false.")
        if enabled and not self._selection_is_available():
            raise ValueError(
                "Choose an available profile before enabling automatic apply."
            )
        settings = replace(self._state.settings, automatic_apply=enabled)
        self._store.save(settings)
        self._state = replace(
            self._state, settings=settings, settings_error=None
        )
        return self._public_state().to_dict()

    async def save_advanced_settings(
        self, draft: Mapping[str, Any]
    ) -> dict[str, Any]:
        validated = validate_advanced_settings(draft)
        settings = replace(self._state.settings, **validated)
        self._store.save(settings)
        self._state = replace(
            self._state, settings=settings, settings_error=None
        )
        self._scan_profiles()
        return self._public_state().to_dict()

    async def apply_selected(self, trigger: str) -> dict[str, Any]:
        try:
            parsed_trigger = ApplyTrigger(trigger)
        except ValueError as error:
            raise ValueError("Trigger must be manual or resume.") from error
        if parsed_trigger not in (ApplyTrigger.MANUAL, ApplyTrigger.RESUME):
            raise ValueError("Trigger must be manual or resume.")

        if parsed_trigger is ApplyTrigger.MANUAL:
            result = await self._manual_application()
        else:
            result = await self._resume_application()
        return result.to_dict()

    async def unload(self) -> None:
        self._unloading = True
        current_task = asyncio.current_task()
        tasks = [
            task
            for task in (
                self._startup_task,
                self._resume_task,
                *self._manual_tasks,
            )
            if task is not None
            and task is not current_task
            and not task.done()
        ]
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def wait_for_startup(self) -> ApplyResult | None:
        """Wait for startup automation, primarily for lifecycle tests."""

        if self._startup_task is None:
            return None
        return await self._startup_task

    def _public_state(self) -> PluginState:
        settings = self._state.settings
        resolved_directory = resolve_profiles_directory(
            self._deck_user_home, settings.profiles_directory_override
        )
        return replace(
            self._state,
            resolved_executable=settings.executable_override or "OpenRGB",
            resolved_profiles_directory=str(resolved_directory),
        )

    def _scan_profiles(self) -> None:
        directory = resolve_profiles_directory(
            self._deck_user_home,
            self._state.settings.profiles_directory_override,
        )
        result = discover_profiles(directory, self._system_profiles_directory)
        self._state = replace(
            self._state,
            profiles=result.profiles,
            discovery_error=result.error,
        )
        if result.successful and not self._selection_is_available():
            settings = self._state.settings
            if settings.selected_profile is not None or settings.automatic_apply:
                reconciled = replace(
                    settings,
                    selected_profile=None,
                    automatic_apply=False,
                )
                self._store.save(reconciled)
                self._state = replace(
                    self._state,
                    settings=reconciled,
                    settings_error=None,
                )

    def _selection_is_available(self) -> bool:
        selected = self._state.settings.selected_profile
        return selected is not None and any(
            profile.identifier == selected for profile in self._state.profiles
        )

    async def _manual_application(self) -> ApplyResult:
        task = asyncio.current_task()
        if task is not None:
            self._manual_tasks.add(task)
        try:
            if self._unloading:
                result = self._unloading_failure(ApplyTrigger.MANUAL)
                self._publish_result(result)
                return result
            precondition = self._selection_failure(ApplyTrigger.MANUAL)
            if precondition is not None:
                self._publish_result(precondition)
                return precondition
            async with self._apply_lock:
                if self._unloading:
                    result = self._unloading_failure(ApplyTrigger.MANUAL)
                else:
                    result = self._selection_failure(ApplyTrigger.MANUAL)
                    if result is None:
                        result = await self._attempt(ApplyTrigger.MANUAL)
            self._publish_result(result)
            return result
        finally:
            if task is not None:
                self._manual_tasks.discard(task)

    async def _resume_application(self) -> ApplyResult:
        if self._unloading:
            result = self._unloading_failure(ApplyTrigger.RESUME)
            self._publish_result(result)
            return result
        if self._resume_task is None or self._resume_task.done():
            self._resume_task = asyncio.create_task(
                self._automatic_sequence(ApplyTrigger.RESUME)
            )
        return await asyncio.shield(self._resume_task)

    async def _automatic_sequence(self, trigger: ApplyTrigger) -> ApplyResult:
        if not self._state.settings.automatic_apply:
            result = self._result(
                False,
                self._state.settings.selected_profile or "",
                trigger,
                "Automatic apply is disabled.",
            )
            self._publish_result(result)
            return result
        precondition = self._selection_failure(trigger)
        if precondition is not None:
            self._publish_result(precondition)
            return precondition

        result: ApplyResult | None = None
        for attempt_number in range(1, AUTOMATIC_ATTEMPTS + 1):
            if self._unloading:
                raise asyncio.CancelledError
            stop_sequence = False
            async with self._apply_lock:
                if self._unloading:
                    raise asyncio.CancelledError
                if not self._state.settings.automatic_apply:
                    result = self._result(
                        False,
                        self._state.settings.selected_profile or "",
                        trigger,
                        "Automatic apply is disabled.",
                    )
                    stop_sequence = True
                else:
                    result = self._selection_failure(trigger)
                    if result is None:
                        result = await self._attempt(trigger)
                    else:
                        stop_sequence = True
            if stop_sequence:
                break
            if result.success:
                break
            self._logger.warning(
                "Automatic OpenRGB %s attempt %d/%d failed: %s",
                trigger.value,
                attempt_number,
                AUTOMATIC_ATTEMPTS,
                result.message,
            )
            if attempt_number < AUTOMATIC_ATTEMPTS:
                await self._sleep(AUTOMATIC_RETRY_SECONDS)

        assert result is not None
        self._publish_result(result)
        return result

    def _selection_failure(self, trigger: ApplyTrigger) -> ApplyResult | None:
        if self._selection_is_available():
            return None
        selected = self._state.settings.selected_profile or ""
        return self._result(
            False,
            selected,
            trigger,
            "Choose an available profile before applying.",
        )

    def _unloading_failure(self, trigger: ApplyTrigger) -> ApplyResult:
        return self._result(
            False,
            self._state.settings.selected_profile or "",
            trigger,
            "The plugin is unloading; no profile was applied.",
        )

    async def _attempt(self, trigger: ApplyTrigger) -> ApplyResult:
        selected = self._state.settings.selected_profile
        assert selected is not None
        arguments = self._build_arguments(selected)
        self._logger.info("Launching OpenRGB for profile %r", selected)
        try:
            process = await self._process_factory(
                *arguments,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except (OSError, RuntimeError, ValueError) as error:
            self._logger.error("Failed to launch OpenRGB: %s", error)
            return self._result(
                False, selected, trigger, "OpenRGB could not be started."
            )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=PROCESS_TIMEOUT_SECONDS
            )
        except asyncio.TimeoutError:
            stdout, stderr = await self._terminate_and_collect(process)
            self._logger.error(
                "OpenRGB timed out for profile %r after %.0f seconds. "
                "stdout=%r stderr=%r",
                selected,
                PROCESS_TIMEOUT_SECONDS,
                _decode_output(stdout),
                _decode_output(stderr),
            )
            return self._result(False, selected, trigger, "OpenRGB timed out.")
        except asyncio.CancelledError:
            await self._terminate_and_collect(process)
            raise

        stdout_text = _decode_output(stdout)
        stderr_text = _decode_output(stderr)
        if process.returncode != 0:
            self._logger.error(
                "OpenRGB exited with status %s. stdout=%r stderr=%r",
                process.returncode,
                stdout_text,
                stderr_text,
            )
            return self._result(
                False,
                selected,
                trigger,
                f"OpenRGB exited with status {process.returncode}.",
            )
        if SUCCESS_MARKER not in stdout_text:
            self._logger.error(
                "OpenRGB did not confirm profile load. stdout=%r stderr=%r",
                stdout_text,
                stderr_text,
            )
            return self._result(
                False,
                selected,
                trigger,
                "OpenRGB did not confirm that the profile was loaded.",
            )
        return self._result(True, selected, trigger, "Profile applied.")

    async def _terminate_and_collect(self, process: Any) -> tuple[Any, Any]:
        try:
            process.terminate()
        except ProcessLookupError:
            pass
        try:
            return await asyncio.wait_for(
                process.communicate(),
                timeout=PROCESS_TERMINATE_GRACE_SECONDS,
            )
        except asyncio.TimeoutError:
            self._logger.warning(
                "OpenRGB did not terminate promptly; killing the child process."
            )
            try:
                process.kill()
            except ProcessLookupError:
                pass
            return await process.communicate()

    def _build_arguments(self, selected: str) -> list[str]:
        settings = self._state.settings
        arguments = [settings.executable_override or "OpenRGB"]
        if settings.remote_enabled:
            arguments.extend(["--client", settings.server_address])
        directory = resolve_profiles_directory(
            self._deck_user_home, settings.profiles_directory_override
        )
        arguments.extend(["--config", str(directory), "--profile", selected])
        return arguments

    def _result(
        self,
        success: bool,
        profile: str,
        trigger: ApplyTrigger,
        message: str,
    ) -> ApplyResult:
        timestamp = self._clock().astimezone(timezone.utc).isoformat().replace(
            "+00:00", "Z"
        )
        return ApplyResult(success, profile, trigger, timestamp, message)

    def _publish_result(self, result: ApplyResult) -> None:
        last_applied = self._state.last_applied
        if result.success:
            last_applied = LastApplied(result.profile, result.timestamp)
        self._state = replace(
            self._state,
            last_result=result,
            last_applied=last_applied,
        )


def _decode_output(value: bytes | str) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value
