"""Bounded loopback preview for one immutable static artifact."""

from __future__ import annotations

import mimetypes
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlsplit


class PreviewServer:
    def __init__(self, store, artifact_digest: str, port: int = 0):
        manifest = store.get_manifest(artifact_digest)
        entry = manifest.spec.entry_document

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                requested = unquote(urlsplit(self.path).path).lstrip("/") or entry
                try:
                    content = store.open_file(artifact_digest, requested)
                except (ValueError, FileNotFoundError):
                    self.send_error(404)
                    return
                media_type = mimetypes.guess_type(requested)[0] or "application/octet-stream"
                self.send_response(200)
                self.send_header("Content-Type", media_type)
                self.send_header("Content-Length", str(len(content)))
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Referrer-Policy", "no-referrer")
                self.send_header("Content-Security-Policy", "default-src 'self'; object-src 'none'; base-uri 'none'")
                self.send_header("Cache-Control", "public, max-age=31536000, immutable")
                self.end_headers()
                self.wfile.write(content)

            def log_message(self, format, *args):
                return

        self.server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    @property
    def address(self):
        return self.server.server_address

    def start(self):
        self.thread.start()
        return self

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def __enter__(self):
        return self.start()

    def __exit__(self, *_):
        self.close()
