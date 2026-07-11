from __future__ import annotations

import asyncio
import sys
import unittest
import os
from pathlib import Path

from fastapi import HTTPException
from starlette.datastructures import QueryParams

FASTAPI_ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("VECTOR_STORAGE_PATH", "/tmp/servicefabric-fastapi-tests")
sys.path.insert(0, str(FASTAPI_ROOT))

from app.api.dependencies.auth import verify_websocket_principal
from app.api.endpoints.websockets import broadcast_event, manager, websocket_endpoint
from app.security.jwt_validator import validate_jwt
from tests.helpers import issue_token


class FakeWebSocket:
    def __init__(self, token: str | None = None):
        self.headers = {"authorization": f"Bearer {token}"} if token else {}
        self.query_params = QueryParams()
        self.close_code = None
        self.accepted = False

    async def close(self, code: int):
        self.close_code = code

    async def accept(self):
        self.accepted = True


class WebSocketSecurityTests(unittest.TestCase):
    def test_websocket_is_rejected_before_accept_without_a_token(self) -> None:
        websocket = FakeWebSocket()
        asyncio.run(websocket_endpoint(websocket, "client-a"))
        self.assertEqual(websocket.close_code, 1008)
        self.assertFalse(websocket.accepted)
        self.assertNotIn(websocket, manager.active_connections)

    def test_websocket_accepts_a_verified_principal(self) -> None:
        token = issue_token()
        principal = asyncio.run(verify_websocket_principal(FakeWebSocket(token)))
        self.assertIsNotNone(principal)
        self.assertEqual(principal.subject, "test-service")

    def test_broadcast_requires_service_authority(self) -> None:
        principal = validate_jwt(issue_token(principal_type="human", scopes=[]))
        with self.assertRaises(HTTPException) as raised:
            asyncio.run(broadcast_event({"event": "changed"}, principal))
        self.assertEqual(raised.exception.status_code, 403)
