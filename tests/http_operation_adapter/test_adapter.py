from __future__ import annotations

import json
import sys
import unittest
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).parents[2] / "packages/servicefabric_http_operation_adapter/src"))

from servicefabric_http_operation_adapter import HttpOperationAdapter, HttpOperationAdapterError  # noqa: E402


@dataclass
class Binding:
    method: str = "POST"
    path: str = "/notes"
    request_content_type: str = "application/json"
    response_content_type: str = "application/json"
    timeout_seconds: int | None = 10


class Response:
    def __init__(self, body: object, content_type: str = "application/json") -> None:
        self.headers = type("Headers", (), {"get_content_type": lambda _: content_type})()
        self._body = json.dumps(body).encode("utf-8")

    def read(self, _: int) -> bytes:
        return self._body

    def __enter__(self) -> "Response":
        return self

    def __exit__(self, *_: object) -> None:
        return None


class HttpOperationAdapterTests(unittest.TestCase):
    def test_posts_json_to_a_literal_loopback_endpoint(self) -> None:
        captured = {}

        def opener(request, timeout):
            captured.update(url=request.full_url, method=request.method, body=request.data, timeout=timeout)
            return Response({"id": 7})

        result = HttpOperationAdapter(opener=opener).invoke("http://127.0.0.1:8123", Binding(), {"title": "one"})
        self.assertEqual(result, {"id": 7})
        self.assertEqual(captured, {"url": "http://127.0.0.1:8123/notes", "method": "POST", "body": b'{"title":"one"}', "timeout": 10})

        result = HttpOperationAdapter(opener=opener).invoke(
            "http://127.0.0.1:8123", Binding(method="GET", path="/notes/{note_id}"), {"note_id": 7, "include": "tags"}
        )
        self.assertEqual(result, {"id": 7})
        self.assertEqual(captured["url"], "http://127.0.0.1:8123/notes/7?include=tags")
        self.assertIsNone(captured["body"])

    def test_rejects_non_loopback_or_unsafe_reviewed_routes(self) -> None:
        adapter = HttpOperationAdapter(opener=lambda *_: Response({}))
        for endpoint, binding in (("http://localhost:8123", Binding()), ("https://127.0.0.1:8123", Binding()), ("http://127.0.0.1:8123", Binding(path="/notes?debug=1")), ("http://127.0.0.1:8123", Binding(method="TRACE")), ("http://127.0.0.1:8123", Binding(timeout_seconds=0))):
            with self.assertRaises(HttpOperationAdapterError) as error:
                adapter.invoke(endpoint, binding, {})
            self.assertIn(error.exception.code, {"invalid_endpoint", "invalid_binding"})

    def test_returns_structured_safe_transport_and_response_errors(self) -> None:
        rejecting = HttpOperationAdapter(opener=lambda request, timeout: (_ for _ in ()).throw(HTTPError(request.full_url, 400, "bad", {}, None)))
        with self.assertRaises(HttpOperationAdapterError) as remote:
            rejecting.invoke("http://127.0.0.1:8123", Binding(), {})
        self.assertEqual(remote.exception.to_dict(), {"code": "remote_rejected", "message": "HTTP operation rejected the request"})

        invalid_json = HttpOperationAdapter(opener=lambda *_: Response({}, "text/plain"))
        with self.assertRaises(HttpOperationAdapterError) as response:
            invalid_json.invoke("http://127.0.0.1:8123", Binding(), {})
        self.assertEqual(response.exception.code, "invalid_response")
