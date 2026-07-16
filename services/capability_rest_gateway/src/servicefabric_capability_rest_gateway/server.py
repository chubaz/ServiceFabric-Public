"""Bounded loopback HTTP server for the capability REST projection."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from urllib.parse import parse_qs, unquote, urlsplit

from .gateway import CapabilityRestGateway


_LOOPBACK_HOST = "127.0.0.1"
_CAPABILITIES_PATH = "/capabilities"
_MAX_BODY_BYTES = 65_536


class LoopbackCapabilityRestServer:
    """Serve a consumer-facade projection on IPv4 loopback only."""

    def __init__(self, gateway: CapabilityRestGateway, *, host: str = _LOOPBACK_HOST, port: int = 0) -> None:
        if host != _LOOPBACK_HOST:
            raise ValueError("capability REST gateway must bind to 127.0.0.1")
        if isinstance(port, bool) or not isinstance(port, int) or not 0 <= port <= 65_535:
            raise ValueError("port must be an integer from 0 through 65535")
        self._gateway = gateway
        self._server = ThreadingHTTPServer((_LOOPBACK_HOST, port), self._handler())
        self._thread: Thread | None = None

    @property
    def endpoint(self) -> str:
        return f"http://{_LOOPBACK_HOST}:{self._server.server_address[1]}"

    def start(self) -> "LoopbackCapabilityRestServer":
        if self._thread is not None:
            raise RuntimeError("capability REST gateway is already started")
        self._thread = Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        return self

    def close(self) -> None:
        if self._thread is not None:
            self._server.shutdown()
            self._thread.join(timeout=2)
            self._thread = None
        self._server.server_close()

    def __enter__(self) -> "LoopbackCapabilityRestServer":
        return self.start()

    def __exit__(self, *_: object) -> None:
        self.close()

    def _handler(self) -> type[BaseHTTPRequestHandler]:
        gateway = self._gateway

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                parsed = urlsplit(self.path)
                try:
                    if parsed.path == _CAPABILITIES_PATH:
                        query = parse_qs(parsed.query, keep_blank_values=True)
                        if set(query) - {"application"} or len(query.get("application", [])) > 1:
                            return self._send(400, {"error": "invalid query"})
                        return self._send(200, gateway.list_capabilities(query.get("application", [None])[0]))
                    capability_id, action = self._capability_route(parsed.path)
                    if parsed.query:
                        return self._send(400, {"error": "invalid query"})
                    if action == "availability":
                        return self._send(200, gateway.availability(capability_id))
                    if action is None:
                        return self._send(200, gateway.describe_capability(capability_id))
                    return self._send(404, {"error": "not found"})
                except Exception as exc:
                    status, payload = _facade_error(exc)
                    return self._send(status, payload)

            def do_POST(self) -> None:
                parsed = urlsplit(self.path)
                try:
                    capability_id, action = self._capability_route(parsed.path)
                    if action != "invoke" or parsed.query:
                        return self._send(404, {"error": "not found"})
                    content_type = self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
                    if content_type != "application/json":
                        return self._send(415, {"error": "content type must be application/json"})
                    length = int(self.headers.get("Content-Length", "0"))
                    if not 0 < length <= _MAX_BODY_BYTES:
                        return self._send(413, {"error": "request body is invalid or too large"})
                    payload = json.loads(self.rfile.read(length))
                    if not isinstance(payload, dict) or set(payload) != {"input"}:
                        return self._send(400, {"error": "request body must contain only input"})
                    return self._send(200, gateway.invoke(capability_id, payload["input"]))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    return self._send(400, {"error": "request could not be processed"})
                except Exception as exc:
                    status, response = _facade_error(exc)
                    return self._send(status, response)

            @staticmethod
            def _capability_route(path: str) -> tuple[str, str | None]:
                prefix = f"{_CAPABILITIES_PATH}/"
                if not path.startswith(prefix):
                    raise LookupError(path)
                remainder, action = path[len(prefix) :], None
                if remainder.endswith("/availability"):
                    remainder, action = remainder[: -len("/availability")], "availability"
                elif remainder.endswith("/invoke"):
                    remainder, action = remainder[: -len("/invoke")], "invoke"
                capability_id = unquote(remainder)
                if not capability_id or "/" in capability_id:
                    raise LookupError(path)
                return capability_id, action

            def _send(self, status: int, payload: object) -> None:
                body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *_: object) -> None:
                pass

        return Handler


def _facade_error(error: Exception) -> tuple[int, dict[str, str]]:
    """Project only documented facade failure categories to bounded responses."""

    if isinstance(error, (LookupError, KeyError)) or type(error).__name__ == "CapabilityNotFoundError":
        return 404, {"error": "capability not found"}
    if isinstance(error, ValueError) or type(error).__name__ == "SchemaValidationError":
        return 400, {"error": "request could not be processed"}
    if type(error).__name__ == "CapabilityUnavailableError":
        return 409, {"error": "capability unavailable"}
    return 500, {"error": "capability request failed"}
