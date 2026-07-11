from __future__ import annotations

import sys
import unittest
import os
from pathlib import Path

from pydantic import ValidationError

FASTAPI_ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("VECTOR_STORAGE_PATH", "/tmp/servicefabric-fastapi-tests")
sys.path.insert(0, str(FASTAPI_ROOT))

from app.core.config import Settings
from app.main import app


class CorsTests(unittest.TestCase):
    def test_configured_origin_is_allowed(self) -> None:
        cors = next(middleware for middleware in app.user_middleware if middleware.cls.__name__ == "CORSMiddleware")
        self.assertIn("http://localhost:3000", cors.kwargs["allow_origins"])
        self.assertTrue(cors.kwargs["allow_credentials"])
        self.assertNotIn("*", cors.kwargs["allow_origins"])

    def test_production_rejects_wildcard_credentialed_cors(self) -> None:
        with self.assertRaises(ValidationError):
            Settings(
                FABRIC_ENVIRONMENT="production",
                JWT_SECRET_KEY="a-secure-secret-with-at-least-thirty-two-characters",
                JWT_ISSUER="https://identity.example.test",
                JWT_AUDIENCE="servicefabric-fastapi",
                CORS_ALLOWED_ORIGINS="*",
            )
