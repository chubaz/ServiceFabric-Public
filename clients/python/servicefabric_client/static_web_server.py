"""Bounded loopback static server used by the reviewed React web handoff."""

from __future__ import annotations

import argparse
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class _Handler(SimpleHTTPRequestHandler):
    root: Path

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, directory=str(self.root), **kwargs)

    def do_GET(self) -> None:  # noqa: N802 - required stdlib hook
        if self.path == "/health":
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"healthy\n")
            return
        super().do_GET()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="servicefabric-static-web")
    parser.add_argument("--root", required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", required=True, type=int)
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    if not root.is_dir():
        raise SystemExit("static web root does not exist")
    if args.host != "127.0.0.1":
        raise SystemExit("static web server only supports loopback")
    _Handler.root = root
    server = ThreadingHTTPServer((args.host, args.port), _Handler)
    try:
        server.serve_forever()
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
