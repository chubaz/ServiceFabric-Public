from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [
    str(ROOT / "clients" / "python"),
    str(ROOT / "packages" / "servicefabric_contracts" / "src"),
]

from servicefabric_client.capsule_cli import execute
from servicefabric_client.capsules import CapsuleClient


class FakeSession:
    def __init__(self):
        self.closed = False
        self.result = type("Result", (), {"model_dump": lambda self, **_: {"status": "open"}})()

    def dispatch(self, method: str, path: str, head_only: bool = False):
        return type("Response", (), {"status": 200, "headers": {"X-Test": "1"}, "body": b"ok"})()

    def close(self):
        self.closed = True


class FakeHostService:
    def __init__(self):
        self.opened = 0
        self.closed = 0

    def open_session(self, request):
        self.opened += 1
        return FakeSession()


class CapsuleClientTests(unittest.TestCase):
    def test_client_delegates_to_host_service(self) -> None:
        client = CapsuleClient(FakeHostService())
        session = client.open_session(object())
        response = client.dispatch(session, "GET", "/")
        self.assertEqual(response.status, 200)
        client.close_session(session)
        self.assertTrue(session.closed)

    def test_cli_emits_deterministic_json(self) -> None:
        request_file = ROOT / "packages" / "servicefabric_contracts" / "tests" / "fixtures" / "capsule_host_request_hello.json"
        output = execute(FakeHostService(), ["open", "--request-file", str(request_file)])
        self.assertEqual(json.loads(output), {"status": "open"})
