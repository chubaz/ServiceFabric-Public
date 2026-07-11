from __future__ import annotations

import asyncio
import logging
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock, patch

FASTAPI_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(FASTAPI_ROOT))

from app.security.jwt_validator import InvalidPrincipalToken, validate_jwt
from app.services.background_tasks import audit_log_event
from tests.helpers import issue_token


class AuthenticationTests(unittest.TestCase):
    def test_valid_token_creates_typed_principal(self) -> None:
        principal = validate_jwt(issue_token())
        self.assertEqual(principal.subject, "test-service")
        self.assertEqual(principal.tenant_id, "tenant-a")
        self.assertIn("fabric:broadcast", principal.scopes)

    def test_invalid_issuer_is_rejected(self) -> None:
        with self.assertRaises(InvalidPrincipalToken):
            validate_jwt(issue_token(iss="untrusted-issuer"))

    def test_invalid_audience_is_rejected(self) -> None:
        with self.assertRaises(InvalidPrincipalToken):
            validate_jwt(issue_token(aud="other-audience"))

    def test_expired_token_is_rejected(self) -> None:
        with self.assertRaises(InvalidPrincipalToken):
            validate_jwt(issue_token(exp=0))

    def test_future_not_before_and_wrong_token_type_are_rejected(self) -> None:
        with self.assertRaises(InvalidPrincipalToken):
            validate_jwt(issue_token(nbf=datetime.now(timezone.utc) + timedelta(minutes=1)))
        with self.assertRaises(InvalidPrincipalToken):
            validate_jwt(issue_token(token_type="access"))

    def test_audit_log_does_not_emit_credential_payload(self) -> None:
        credential = issue_token()
        logger = logging.getLogger("app.services.background_tasks")
        with self.assertLogs(logger, level="INFO") as captured, patch(
            "app.services.background_tasks.asyncio.sleep", new=AsyncMock()
        ):
            asyncio.run(audit_log_event("FabricGateway", "dashboard_accessed", {"token": credential}))
        self.assertNotIn(credential, "\n".join(captured.output))
