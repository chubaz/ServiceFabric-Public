"""Bounded execution target references. This module contains no execution code."""

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import Field, field_validator, model_validator

from .common import Identifier, ImmutableContractModel


class NativeFunctionBinding(ImmutableContractModel):
    binding_kind: Literal["native_function"]
    service_package_id: Identifier
    entrypoint_id: Identifier
    function_ref: Identifier


class NativeServiceBinding(ImmutableContractModel):
    binding_kind: Literal["native_service"]
    service_package_id: Identifier
    entrypoint_id: Identifier
    operation_ref: Identifier


class InternalGraphBinding(ImmutableContractModel):
    binding_kind: Literal["internal_graph"]
    graph_revision_ref: str = Field(min_length=3, max_length=256, pattern=r"^graph://[a-z][a-z0-9._:/-]+$")


class ExternalHttpBinding(ImmutableContractModel):
    binding_kind: Literal["external_http"]
    service_package_id: Identifier | None = None
    external_binding_ref: Identifier | None = None
    path_template: str = Field(min_length=1, max_length=256, pattern=r"^/[A-Za-z0-9_{}./-]*$")
    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"]
    credential_binding_ref: Identifier | None = None

    @model_validator(mode="after")
    def validate_owner_reference(self) -> "ExternalHttpBinding":
        if (self.service_package_id is None) == (self.external_binding_ref is None):
            raise ValueError("external HTTP binding requires exactly one package or external binding reference")
        return self


class DatabaseOperationBinding(ImmutableContractModel):
    binding_kind: Literal["database_operation"]
    service_package_id: Identifier
    entrypoint_id: Identifier
    operation_id: Identifier


class CommandArgumentMapping(ImmutableContractModel):
    argument: Identifier
    input_field_ref: str = Field(min_length=7, max_length=160, pattern=r"^input\.[a-z][a-z0-9_.-]*$")


class CommandRunnerBinding(ImmutableContractModel):
    binding_kind: Literal["command_runner"]
    service_package_id: Identifier
    entrypoint_id: Identifier
    command_name: Identifier
    argument_mapping: tuple[CommandArgumentMapping, ...] = Field(default_factory=tuple, max_length=64)

    @field_validator("argument_mapping")
    @classmethod
    def validate_argument_mapping(cls, mapping: tuple[CommandArgumentMapping, ...]) -> tuple[CommandArgumentMapping, ...]:
        arguments = [item.argument for item in mapping]
        if len(set(arguments)) != len(arguments):
            raise ValueError("command argument mappings must be unique")
        return mapping


class FederatedMcpBinding(ImmutableContractModel):
    binding_kind: Literal["federated_mcp"]
    external_package_id: Identifier
    remote_tool_name: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_.\-/]+$")
    projection_policy: Literal["explicit_selection", "reviewed_selection"]


class HumanTaskBinding(ImmutableContractModel):
    binding_kind: Literal["human_task"]
    workflow_ref: Identifier
    task_type: Identifier
    result_handling: Literal["human_validated"]


ExecutionBinding = Annotated[
    Union[
        NativeFunctionBinding,
        NativeServiceBinding,
        InternalGraphBinding,
        ExternalHttpBinding,
        DatabaseOperationBinding,
        CommandRunnerBinding,
        FederatedMcpBinding,
        HumanTaskBinding,
    ],
    Field(discriminator="binding_kind"),
]
