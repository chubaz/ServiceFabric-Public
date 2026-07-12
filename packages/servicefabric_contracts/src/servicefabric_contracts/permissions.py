"""Opaque permission and approval policy references."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, field_validator

from .common import Identifier, ImmutableContractModel


class PermissionRequirement(ImmutableContractModel):
    permission_id: Identifier
    tenant_scope: Literal["caller_tenant", "owner_tenant", "platform", "explicit"]
    resource_scope: str = Field(min_length=1, max_length=256)
    delegation_allowed: bool = False


class PermissionContract(ImmutableContractModel):
    permissions: tuple[PermissionRequirement, ...] = Field(default_factory=tuple, max_length=64)

    @field_validator("permissions")
    @classmethod
    def unique_permissions(cls, permissions: tuple[PermissionRequirement, ...]) -> tuple[PermissionRequirement, ...]:
        identifiers = [permission.permission_id for permission in permissions]
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("permission declarations must be unique")
        return permissions
