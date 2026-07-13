"""Run the bounded local research-demo gateway process."""

from __future__ import annotations

import argparse
from pathlib import Path

from servicefabric_runtime.portfolio import __file__ as portfolio_module

from .server import LoopbackGatewayServer
from .service import LocalConsumerGateway


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="servicefabric-gateway")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)
    root = Path(portfolio_module).resolve().parent.parent / "portfolios"
    with LoopbackGatewayServer(LocalConsumerGateway(root), port=args.port) as server:
        print(server.endpoint, flush=True)
        try:
            server._thread.join()
        except KeyboardInterrupt:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
