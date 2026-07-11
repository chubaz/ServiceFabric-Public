from __future__ import annotations

from fastapi import Header, HTTPException, status
from starlette.websockets import WebSocket

from app.security.jwt_validator import InvalidPrincipalToken, validate_jwt
from app.security.principal import PrincipalContext


def _bearer_token(authorization: str | None) -> str:
    if not authorization:
        raise InvalidPrincipalToken("missing credential")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise InvalidPrincipalToken("invalid credential scheme")
    return token


async def verify_fabric_token(authorization: str | None = Header(default=None)) -> PrincipalContext:
    try:
        return validate_jwt(_bearer_token(authorization))
    except InvalidPrincipalToken as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def require_tenant(principal: PrincipalContext) -> PrincipalContext:
    if not principal.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant identity is required")
    return principal


def require_service_scope(principal: PrincipalContext, scope: str) -> PrincipalContext:
    if principal.principal_type != "service" or scope not in principal.scopes:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient authority")
    return principal


async def verify_websocket_principal(websocket: WebSocket) -> PrincipalContext | None:
    authorization = websocket.headers.get("authorization")
    try:
        return validate_jwt(_bearer_token(authorization))
    except InvalidPrincipalToken:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None
