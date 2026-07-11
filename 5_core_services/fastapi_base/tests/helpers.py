from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import settings


def issue_token(**overrides: object) -> str:
    claims: dict[str, object] = {
        "sub": "test-service",
        "principal_type": "service",
        "tenant_id": "tenant-a",
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
        "token_type": settings.JWT_TOKEN_TYPE,
        "scopes": ["fabric:broadcast"],
        "nbf": datetime.now(timezone.utc) - timedelta(seconds=1),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
    }
    claims.update(overrides)
    return jwt.encode(claims, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
