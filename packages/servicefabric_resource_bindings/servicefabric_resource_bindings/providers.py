"""Static local resource provider used by development binding plans."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from urllib.parse import urlparse

from servicefabric_resource_bindings.errors import (
    DuplicateResourceBinding,
    InvalidResourceBinding,
    ResourceBindingNotFound,
    ResourceBindingTypeMismatch,
)
from servicefabric_resource_bindings.identifiers import (
    environment_key_for,
    validate_environment_key,
    validate_resource_id,
)
from servicefabric_resource_bindings.models import (
    BoundResource,
    LocalResourceDefinition,
    ResourceBindingRequest,
)

_OPAQUE_SECRET_PREFIXES = ("secret://", "servicefabric-secret:")
_LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1"}


class StaticLocalResourceProvider:
    """Provider backed by reviewed in-memory local resource definitions."""

    def __init__(self, definitions: Iterable[LocalResourceDefinition]) -> None:
        bindings: dict[str, LocalResourceDefinition] = {}
        for definition in definitions:
            normalized = _validate_definition(definition)
            if normalized.id in bindings:
                raise DuplicateResourceBinding(
                    f"local resource binding '{normalized.id}' is already registered"
                )
            bindings[normalized.id] = normalized
        self._definitions = bindings

    def can_bind(self, request: ResourceBindingRequest) -> bool:
        """Return whether this provider has a binding with the requested id."""

        return request.id in self._definitions

    def bind(self, request: ResourceBindingRequest) -> BoundResource:
        """Bind a request, validating type and scope compatibility."""

        definition = self._definitions.get(request.id)
        if definition is None:
            raise ResourceBindingNotFound(
                f"local resource binding '{request.id}' is not registered"
            )
        if definition.type != request.type:
            raise ResourceBindingTypeMismatch(
                f"local resource binding '{request.id}' has type "
                f"'{definition.type}', not '{request.type}'"
            )
        if definition.scope != request.scope:
            raise ResourceBindingTypeMismatch(
                f"local resource binding '{request.id}' has scope "
                f"'{definition.scope}', not '{request.scope}'"
            )
        return _bound_resource(definition)


def _validate_definition(definition: LocalResourceDefinition) -> LocalResourceDefinition:
    resource_id = validate_resource_id(definition.id)
    _validate_simple_token(definition.type, "resource type")
    _validate_simple_token(definition.scope, "resource scope")
    _validate_simple_token(definition.provider_id, "provider id")
    if definition.readiness not in {"ready", "pending", "unavailable"}:
        raise InvalidResourceBinding("resource readiness must be ready, pending, or unavailable")

    if definition.endpoint is not None:
        _validate_loopback_endpoint(definition.endpoint)

    _validate_environment(definition.environment)
    _validate_secret_refs(definition.secret_refs)
    return LocalResourceDefinition(
        id=resource_id,
        type=definition.type,
        scope=definition.scope,
        provider_id=definition.provider_id,
        endpoint=definition.endpoint,
        environment=dict(sorted(definition.environment.items())),
        secret_refs=dict(sorted(definition.secret_refs.items())),
        readiness=definition.readiness,
    )


def _bound_resource(definition: LocalResourceDefinition) -> BoundResource:
    environment = dict(definition.environment)
    if definition.endpoint is not None:
        environment[environment_key_for(definition.id, "URL")] = definition.endpoint

    secret_refs = {
        environment_key_for(definition.id, key): value
        for key, value in definition.secret_refs.items()
    }
    return BoundResource(
        id=definition.id,
        type=definition.type,
        scope=definition.scope,
        provider_id=definition.provider_id,
        environment=dict(sorted(environment.items())),
        secret_refs=dict(sorted(secret_refs.items())),
        readiness=definition.readiness,
    )


def _validate_simple_token(value: str, field: str) -> None:
    if (
        not isinstance(value, str)
        or not value
        or len(value) > 128
        or any(character.isspace() for character in value)
    ):
        raise InvalidResourceBinding(f"{field} must be a non-empty token")


def _validate_environment(environment: Mapping[str, str]) -> None:
    for key, value in environment.items():
        validate_environment_key(key)
        if not isinstance(value, str):
            raise InvalidResourceBinding(f"environment value for '{key}' must be a string")


def _validate_secret_refs(secret_refs: Mapping[str, str]) -> None:
    for key, value in secret_refs.items():
        validate_environment_key(environment_key_for("resource", key))
        if not isinstance(value, str) or not value.startswith(_OPAQUE_SECRET_PREFIXES):
            raise InvalidResourceBinding(
                f"secret reference '{key}' must be an opaque ServiceFabric secret reference"
            )


def _validate_loopback_endpoint(endpoint: str) -> None:
    parsed = urlparse(endpoint)
    if parsed.scheme not in {"http", "https", "postgresql", "redis"}:
        raise InvalidResourceBinding("resource endpoint scheme is not supported locally")
    if parsed.username or parsed.password:
        raise InvalidResourceBinding("resource endpoint must not contain literal credentials")
    if parsed.hostname not in _LOOPBACK_HOSTS:
        raise InvalidResourceBinding("resource endpoint must use a loopback host")
