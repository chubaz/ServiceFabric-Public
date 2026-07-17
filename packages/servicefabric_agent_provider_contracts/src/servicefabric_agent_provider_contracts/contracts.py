"""Immutable provider boundary contracts; no execution behavior lives here."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Protocol

from pydantic import ConfigDict, Field, field_validator
from servicefabric_agentic_contracts import AgentTaskResult
from servicefabric_contracts.common import Identifier, ImmutableContractModel, has_secret_like_key, is_json_value


class _ProviderContract(ImmutableContractModel):
    model_config = ImmutableContractModel.model_config | ConfigDict(populate_by_name=True)


class ProviderExecutionRequest(_ProviderContract):
    run_id: Identifier
    task_id: Identifier
    provider_id: Identifier
    repository: str = Field(min_length=1, max_length=4096)
    prompt: str = Field(min_length=1, max_length=100_000)
    timeout_seconds: int = Field(ge=1, le=86_400)
    maximum_turns: int | None = Field(default=None, ge=1, le=10_000)
    model: str | None = Field(default=None, min_length=1, max_length=256)
    environment_names: tuple[str, ...] = Field(default_factory=tuple, max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("environment_names")
    @classmethod
    def _environment_names_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if any(not name or "=" in name or "\x00" in name for name in value):
            raise ValueError("environment_names must contain names, not values")
        return value

    @field_validator("metadata")
    @classmethod
    def _metadata_is_non_secret_json(cls, value: dict[str, Any]) -> dict[str, Any]:
        def validate(item: object) -> None:
            if isinstance(item, dict):
                for key, nested in item.items():
                    if has_secret_like_key(key):
                        raise ValueError("metadata must not contain provider credentials")
                    validate(nested)
            elif isinstance(item, list):
                for nested in item:
                    validate(nested)
        if not is_json_value(value):
            raise ValueError("metadata must be JSON-compatible")
        validate(value)
        return value


class ProviderRunHandle(_ProviderContract):
    provider_id: Identifier
    run_id: Identifier
    task_id: Identifier
    provider_session_id: str | None = Field(default=None, min_length=1, max_length=512)
    process_id: int | None = Field(default=None, ge=1)
    state: Literal["pending", "running", "success", "failed", "cancelled", "unknown"]


class ProviderEvent(_ProviderContract):
    sequence: int = Field(ge=0)
    event_type: Literal["init", "message", "tool_use", "tool_result", "usage", "result", "warning", "error"]
    timestamp: datetime
    payload: dict[str, Any] = Field(default_factory=dict)


class ProviderUsage(_ProviderContract):
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    cached_tokens: int = Field(default=0, ge=0)
    estimated_cost: float = Field(default=0.0, ge=0)
    duration_ms: int = Field(default=0, ge=0)


class ProviderExecutionResult(_ProviderContract):
    handle: ProviderRunHandle
    status: Literal["success", "failed", "blocked", "cancelled", "timeout", "unknown"]
    task_result: AgentTaskResult | None = None
    usage: ProviderUsage = Field(default_factory=ProviderUsage)
    events_artifact: str | None = Field(default=None, min_length=1, max_length=512)
    stderr_artifact: str | None = Field(default=None, min_length=1, max_length=512)


class ProviderPolicy(_ProviderContract):
    default_provider: Identifier
    role_overrides: dict[str, Identifier] = Field(default_factory=dict)
    maximum_parallel_per_provider: int = Field(ge=1, le=64)
    maximum_total_cost: float | None = Field(default=None, ge=0)
    timeout_seconds: int = Field(ge=1, le=86_400)
    maximum_turns: int | None = Field(default=None, ge=1, le=10_000)

    def provider_for_role(self, role: str) -> str:
        """Resolve a deterministic policy choice without inspecting a provider."""
        return self.role_overrides.get(role, self.default_provider)


class ExecutableHarnessAdapter(Protocol):
    """Translate a canonical request; the runtime owns all subprocess behavior."""

    @property
    def provider_id(self) -> str: ...

    def probe(self) -> dict[str, Any]: ...

    def build_argv(self, request: ProviderExecutionRequest) -> tuple[str, ...]: ...

    def parse_event(self, raw_event: str, sequence: int) -> ProviderEvent | None: ...

    def recover_result(
        self,
        handle: ProviderRunHandle,
        events: tuple[ProviderEvent, ...],
        usage: ProviderUsage,
        *,
        exit_code: int | None,
    ) -> ProviderExecutionResult: ...
