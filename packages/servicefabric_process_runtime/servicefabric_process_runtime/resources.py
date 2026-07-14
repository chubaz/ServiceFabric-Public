"""Process memory and CPU consumption measurement utility."""

from __future__ import annotations

import os
import time
from pathlib import Path

from servicefabric_process_runtime.identity import get_process_fields


def measure_memory_bytes(pid: int) -> int | None:
    """Reads VmRSS of the given process PID on Linux.

    Returns:
        RSS memory usage in bytes, or None if unavailable/unparseable.
    """
    try:
        status_path = Path(f"/proc/{pid}/status")
        if status_path.is_file():
            for line in status_path.read_text(encoding="utf-8").splitlines():
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) * 1024
    except (OSError, ValueError, IndexError):
        pass
    return None


def measure_cpu_percent(pid: int) -> float | None:
    """Calculates CPU usage percentage of a process over a 50ms interval on Linux.

    Returns:
        The CPU usage percentage rounded to 3 decimal places, or None if unavailable.
    """
    try:
        clock_ticks = os.sysconf("SC_CLK_TCK")
        before_fields = get_process_fields(pid)
        if not before_fields:
            return None
        
        started = time.monotonic()
        time.sleep(0.05)
        
        after_fields = get_process_fields(pid)
        if not after_fields or after_fields[1] != before_fields[1]:
            return None
            
        return round(
            ((after_fields[2] - before_fields[2]) / clock_ticks)
            / (time.monotonic() - started)
            * 100,
            3,
        )
    except (OSError, ValueError, IndexError):
        return None
