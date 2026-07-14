"""Process identity tracking, parsing, and ownership verification."""

from __future__ import annotations

import os
from pathlib import Path


def get_process_fields(pid: int) -> tuple[str, int, int] | None:
    """Reads and parses the state, start ticks, and CPU times of a process on Linux.

    Returns:
        A tuple of (process_state, process_start_ticks, cpu_ticks) if successful, None otherwise.
    """
    try:
        text = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")
        # Skip the parenthesized executable name safely to avoid split errors
        fields = text[text.rfind(")") + 2 :].split()
        return fields[0], int(fields[19]), int(fields[11]) + int(fields[12])
    except (OSError, ValueError, IndexError):
        return None


def is_alive(pid: int) -> bool:
    """Checks if the given PID represents an active, non-zombie process."""
    fields = get_process_fields(pid)
    return bool(fields and fields[0] != "Z")


def is_same_process(pid: int, expected_start: int) -> bool:
    """Checks if the active process has the exact same start ticks (combating PID reuse)."""
    fields = get_process_fields(pid)
    return bool(fields and fields[0] != "Z" and fields[1] == expected_start)


def is_owned_process(
    pid: int, expected_start: int, expected_executable: Path, expected_args: list[str]
) -> bool:
    """Verifies that the process has the exact expected executable and command arguments."""
    if not is_same_process(pid, expected_start):
        return False
    try:
        command = Path(f"/proc/{pid}/cmdline").read_bytes().split(b"\0")
        if command and command[-1] == b"":
            command.pop()
    except OSError:
        return False

    expected = [os.fsencode(str(expected_executable))] + [
        os.fsencode(arg) for arg in expected_args
    ]
    return command[: len(expected)] == expected
