"""Declarative runtime requirement models; no deployment behavior is implemented here."""

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import Field, model_validator

from .common import ContractModel, Identifier, has_secret_like_key


class ConfigReference(ContractModel):
    config_ref: str = Field(min_length=3, max_length=256, pattern=r"^[a-z][a-z0-9._:/-]+$")
    purpose: str = Field(min_length=1, max_length=160)
    optional: bool = False


class SecretReference(ContractModel):
    secret_ref: str = Field(min_length=3, max_length=256, pattern=r"^secret://[a-z][a-z0-9._:/-]+$")
    purpose: str = Field(min_length=1, max_length=160)
    optional: bool = False

    @model_validator(mode="after")
    def reject_literal_secret_fields(self) -> "SecretReference":
        if has_secret_like_key(self.purpose):
            raise ValueError("secret purpose must describe use, not credential material")
        return self


class ComputeRequirements(ContractModel):
    cpu_millicores: int | None = Field(default=None, ge=1, le=64000)
    memory_mebibytes: int | None = Field(default=None, ge=16, le=1048576)


class NetworkPolicy(ContractModel):
    mode: Literal["none", "egress_allowlist", "platform_default"] = "none"
    egress_allowlist: list[str] = Field(default_factory=list, max_length=64)

    @model_validator(mode="after")
    def validate_allowlist(self) -> "NetworkPolicy":
        if self.mode == "egress_allowlist" and not self.egress_allowlist:
            raise ValueError("egress_allowlist mode requires destinations")
        if self.mode != "egress_allowlist" and self.egress_allowlist:
            raise ValueError("destinations are only valid for egress_allowlist mode")
        return self


class StorageRequirement(ContractModel):
    name: Identifier
    persistence: Literal["ephemeral", "persistent"]
    access_mode: Literal["read_only", "read_write"]
    mount_purpose: str = Field(min_length=1, max_length=160)
    capacity_hint_mebibytes: int | None = Field(default=None, ge=1)


class NoHealthProbe(ContractModel):
    probe_kind: Literal["none"]


class HttpHealthProbe(ContractModel):
    probe_kind: Literal["http"]
    path: str = Field(min_length=1, max_length=256, pattern=r"^/")
    expected_status: int = Field(default=200, ge=100, le=599)


class CommandHealthProbe(ContractModel):
    probe_kind: Literal["command"]
    command: list[str] = Field(min_length=1, max_length=32)


class ExternalHealthProbe(ContractModel):
    probe_kind: Literal["external"]
    health_ref: str = Field(min_length=3, max_length=256, pattern=r"^[a-z][a-z0-9._:/-]+$")


HealthDeclaration = Annotated[
    Union[NoHealthProbe, HttpHealthProbe, CommandHealthProbe, ExternalHealthProbe],
    Field(discriminator="probe_kind"),
]


class RuntimeRequirements(ContractModel):
    compute: ComputeRequirements | None = None
    config_refs: list[ConfigReference] = Field(default_factory=list, max_length=64)
    secret_refs: list[SecretReference] = Field(default_factory=list, max_length=64)
