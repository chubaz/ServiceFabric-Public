from __future__ import annotations

import re
from pathlib import Path


IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")


class ServiceAccessDenied(ValueError):
    """Raised when a legacy service target does not satisfy containment policy."""


def validate_identifier(value: object) -> str:
    if not isinstance(value, str) or not IDENTIFIER_PATTERN.fullmatch(value):
        raise ServiceAccessDenied("Invalid service target")
    return value


def resolve_service_directory(root: Path, service_name: object) -> Path:
    name = validate_identifier(service_name)
    resolved_root = root.resolve()
    candidate = (resolved_root / name).resolve()
    if candidate.parent != resolved_root:
        raise ServiceAccessDenied("Invalid service target")
    return candidate


def resolve_tenant_directory(root: Path, tenant_id: object) -> Path:
    tenant = validate_identifier(str(tenant_id))
    resolved_root = root.resolve()
    candidate = (resolved_root / tenant).resolve()
    if candidate.parent != resolved_root:
        raise ServiceAccessDenied("Invalid tenant path")
    return candidate
