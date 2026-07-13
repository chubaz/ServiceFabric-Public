"""Bounded loopback JSON process for the local consumer gateway."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

from .service import LocalConsumerGateway


class LoopbackGatewayServer:
    def __init__(self, gateway: LocalConsumerGateway, *, port: int = 0):
        self._gateway = gateway
        self._server = ThreadingHTTPServer(("127.0.0.1", port), self._handler())
        self._thread: Thread | None = None

    @property
    def endpoint(self) -> str:
        return f"http://127.0.0.1:{self._server.server_address[1]}"

    def _handler(self):
        gateway = self._gateway

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path != "/v1/toolsets/research-demo/tools":
                    return self._send(404, {"error": "not found"})
                return self._send(200, {"tools": list(gateway.list_tools())})

            def do_POST(self):
                prefix = "/v1/toolsets/research-demo/tools/"
                if not self.path.startswith(prefix) or not self.path.endswith(":invoke"):
                    return self._send(404, {"error": "not found"})
                length = int(self.headers.get("Content-Length", "0"))
                if length < 1 or length > 65536:
                    return self._send(413, {"error": "request body is invalid or too large"})
                try:
                    payload = json.loads(self.rfile.read(length))
                    result = gateway.invoke(self.path[len(prefix):-7], payload["arguments"])
                    return self._send(200, result.model_dump(mode="json", by_alias=True))
                except Exception:
                    return self._send(400, {"error": "request could not be processed"})

            def _send(self, status, payload):
                body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *_):
                return

        return Handler

    def start(self):
        self._thread = Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        return self

    def close(self):
        self._server.shutdown(); self._server.server_close()
        if self._thread: self._thread.join(timeout=2)

    def __enter__(self): return self.start()
    def __exit__(self, *_): self.close()
