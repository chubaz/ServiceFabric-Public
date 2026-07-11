from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class PrincipalContext(BaseModel):
    """Identity derived from a validated token, never from caller-supplied request data."""

    subject: str = Field(min_length=1)
    principal_type: Literal["human", "service"]
    tenant_id: str | None = Field(default=None, min_length=1)
    issuer: str
    audience: str
    scopes: frozenset[str] = Field(default_factory=frozenset)
