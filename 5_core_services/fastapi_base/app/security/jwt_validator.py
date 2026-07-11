from __future__ import annotations

from typing import Any

import jwt
from jwt import InvalidTokenError

from app.core.config import settings
from app.security.principal import PrincipalContext


class InvalidPrincipalToken(Exception):
    """Raised when a credential cannot establish a trusted principal."""


def validate_jwt(token: str) -> PrincipalContext:
    try:
        claims: dict[str, Any] = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            issuer=settings.JWT_ISSUER,
            audience=settings.JWT_AUDIENCE,
            options={"require": ["exp", "nbf", "sub", "iss", "aud", "token_type"]},
        )
    except InvalidTokenError as exc:
        raise InvalidPrincipalToken("credential validation failed") from exc

    if claims.get("token_type") != settings.JWT_TOKEN_TYPE:
        raise InvalidPrincipalToken("credential has an invalid token type")

    scopes_claim = claims.get("scopes", claims.get("scope", []))
    if isinstance(scopes_claim, str):
        scopes = frozenset(scope for scope in scopes_claim.split(" ") if scope)
    elif isinstance(scopes_claim, list) and all(isinstance(scope, str) for scope in scopes_claim):
        scopes = frozenset(scopes_claim)
    else:
        raise InvalidPrincipalToken("credential has invalid scopes")

    try:
        return PrincipalContext(
            subject=claims["sub"],
            principal_type=claims["principal_type"],
            tenant_id=claims.get("tenant_id"),
            issuer=claims["iss"],
            audience=settings.JWT_AUDIENCE,
            scopes=scopes,
        )
    except (KeyError, ValueError) as exc:
        raise InvalidPrincipalToken("credential has invalid principal claims") from exc
