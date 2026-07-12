"""Hosting declarations are independent from entrypoint exposure."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from .common import ContractModel

HostingMode = Literal[
    "managed_container",
    "managed_process",
    "managed_static",
    "managed_graph",
    "external_service",
    "external_mcp",
    "none",
]


class ManagedResourceRequirements(ContractModel):
    cpu_millicores: int | None = Field(default=None, ge=1, le=64000)
    memory_mebibytes: int | None = Field(default=None, ge=16, le=1048576)


class HostingDeclaration(ContractModel):
    mode: HostingMode
    managed_resources: ManagedResourceRequirements | None = None
