"""Validation for the atomic advanced-settings operation."""

from __future__ import annotations

import ipaddress
import re
from pathlib import Path
from typing import Any, Mapping


ADVANCED_FIELDS = (
    "executable_override",
    "profiles_directory_override",
    "remote_enabled",
    "server_address",
)


class AdvancedSettingsValidationError(ValueError):
    """One or more advanced-setting fields are invalid."""

    def __init__(self, field_errors: Mapping[str, str]):
        super().__init__("Advanced settings are invalid.")
        self.field_errors = dict(field_errors)


def validate_advanced_settings(draft: Mapping[str, Any]) -> dict[str, Any]:
    errors: dict[str, str] = {}
    if not isinstance(draft, Mapping):
        raise AdvancedSettingsValidationError({"draft": "Expected an object."})

    executable = _string_value(draft, "executable_override", errors)
    profiles_directory = _string_value(
        draft, "profiles_directory_override", errors
    )
    server_address = _string_value(draft, "server_address", errors)
    remote_enabled = draft.get("remote_enabled")
    if not isinstance(remote_enabled, bool):
        errors["remote_enabled"] = "Expected true or false."

    if executable and not Path(executable).is_absolute():
        errors["executable_override"] = "Executable path must be absolute."
    if profiles_directory and not Path(profiles_directory).is_absolute():
        errors["profiles_directory_override"] = (
            "Profiles directory must be absolute."
        )
    if remote_enabled is True:
        if not server_address:
            errors["server_address"] = "Server address is required."
        elif not _valid_server_address(server_address):
            errors["server_address"] = "Enter a valid host and optional port."

    if errors:
        raise AdvancedSettingsValidationError(errors)
    return {
        "executable_override": executable,
        "profiles_directory_override": profiles_directory,
        "remote_enabled": remote_enabled,
        "server_address": server_address,
    }


def _string_value(
    draft: Mapping[str, Any], name: str, errors: dict[str, str]
) -> str:
    value = draft.get(name)
    if not isinstance(value, str):
        errors[name] = "Expected text."
        return ""
    return value


def _valid_server_address(value: str) -> bool:
    if any(character.isspace() for character in value):
        return False

    if value.startswith("["):
        closing = value.find("]")
        if closing < 0:
            return False
        host = value[1:closing]
        suffix = value[closing + 1 :]
        try:
            if ipaddress.ip_address(host).version != 6:
                return False
        except ValueError:
            return False
        return not suffix or (
            suffix.startswith(":") and _valid_port(suffix[1:])
        )

    if value.count(":") > 1:
        try:
            return ipaddress.ip_address(value).version == 6
        except ValueError:
            return False

    host, separator, port = value.rpartition(":")
    if not separator:
        host = value
    elif not _valid_port(port):
        return False

    if not host:
        return False
    try:
        return ipaddress.ip_address(host).version == 4
    except ValueError:
        return bool(
            len(host) <= 253
            and re.fullmatch(
                r"(?=.{1,253}\Z)(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}"
                r"[A-Za-z0-9])?)(?:\.(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}"
                r"[A-Za-z0-9])?))*\.?",
                host,
            )
        )


def _valid_port(value: str) -> bool:
    return value.isdecimal() and 1 <= int(value) <= 65535
