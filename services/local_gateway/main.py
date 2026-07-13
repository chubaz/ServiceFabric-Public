"""Run the bounded local research-demo gateway process."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from servicefabric_runtime.portfolio import __file__ as portfolio_module

from .server import LoopbackGatewayServer
from .service import LocalConsumerGateway


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="servicefabric-gateway")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path(os.environ.get("SERVICEFABRIC_HOME", ".servicefabric")),
        help="local ServiceFabric workspace (default: SERVICEFABRIC_HOME or .servicefabric)",
    )
    args = parser.parse_args(argv)
    root = Path(portfolio_module).resolve().parent.parent / "portfolios"
    workspace = args.workspace.expanduser().resolve(strict=False)
    workspace.mkdir(parents=True, exist_ok=True)
    with LoopbackGatewayServer(LocalConsumerGateway(root, workspace_root=workspace), port=args.port) as server:
        print(server.endpoint, flush=True)
        try:
            server._thread.join()
        except KeyboardInterrupt:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
