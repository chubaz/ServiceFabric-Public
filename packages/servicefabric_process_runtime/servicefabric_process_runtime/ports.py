"""Dynamic loopback port allocation utility."""

from __future__ import annotations

import socket

from servicefabric_process_runtime.errors import PortAllocationError


def allocate_loopback_port() -> int:
    """Dynamically allocates an unused loopback TCP port using OS port binding (port 0).

    Returns:
        The allocated TCP port number.

    Raises:
        PortAllocationError: If port allocation fails.
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Bind specifically to 127.0.0.1 loopback
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
        sock.close()
        return port
    except Exception as exc:
        raise PortAllocationError(
            f"Failed to dynamically allocate loopback port: {exc}"
        ) from exc
