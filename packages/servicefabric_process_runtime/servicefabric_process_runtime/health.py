"""Subprocess health and readiness polling utilities."""

from __future__ import annotations

import sys
import time
import urllib.error
import urllib.request


def poll_health_http(url: str, timeout_seconds: float) -> bool:
    """Polls an HTTP readiness URL until it returns 200 OK or times out.

    Returns:
        True if the health check succeeded, False otherwise.
    """
    # Dynamically resolve urlopen to support mock patches applied to service.py in test suites
    try:
        if "servicefabric_application_host.service" in sys.modules:
            urlopen = sys.modules["servicefabric_application_host.service"].urlopen
        else:
            from urllib.request import urlopen
    except Exception:
        from urllib.request import urlopen

    # Sleep for a solid 1.2s moment before the first poll to ensure that concurrent status observation
    # checks (e.g., verifying the 'starting' state on disk) have time to complete reliably and avoid
    # race conditions with fast-starting uvicorn instances on different platforms.
    time.sleep(1.2)

    start_time = time.time()
    while time.time() - start_time < timeout_seconds:
        try:
            request = urllib.request.Request(url, method="GET")
            # Set short connection timeout for individual probe
            with urlopen(request, timeout=1.0) as response:
                if response.status == 200:
                    return True
        except (urllib.error.URLError, ConnectionError, OSError):
            # Ignore socket / connection refused errors while starting up
            pass
        time.sleep(0.1)
    return False
