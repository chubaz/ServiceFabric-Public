from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class HttpBinding:
    binding_id: str
    method: str
    path: str
    request_schema_ref: str | None = None
    response_schema_ref: str | None = None
    request_content_type: str = "application/json"
    response_content_type: str = "application/json"
    timeout_seconds: int | None = None


@dataclass(frozen=True)
class OperationDefinition:
    operation_id: str
    version: str
    application_ref: str
    module_ref: str
    interface_ref: str
    bindings: tuple[HttpBinding, ...]
    name: str | None = None
    description: str | None = None

    def to_dict(self) -> dict[str, Any]:
        metadata: dict[str, Any] = {"id": self.operation_id, "version": self.version}
        if self.name is not None:
            metadata["name"] = self.name
        if self.description is not None:
            metadata["description"] = self.description
        return {
            "apiVersion": "servicefabric.local/v1",
            "kind": "OperationDefinition",
            "metadata": metadata,
            "spec": {
                "application_ref": self.application_ref,
                "module_ref": self.module_ref,
                "interface_ref": self.interface_ref,
                "bindings": [
                    {
                        "id": binding.binding_id,
                        "protocol": "http",
                        "method": binding.method,
                        "path": binding.path,
                        **({"request_schema_ref": binding.request_schema_ref} if binding.request_schema_ref is not None else {}),
                        **({"response_schema_ref": binding.response_schema_ref} if binding.response_schema_ref is not None else {}),
                        "request_content_type": binding.request_content_type,
                        "response_content_type": binding.response_content_type,
                        **({"timeout_seconds": binding.timeout_seconds} if binding.timeout_seconds is not None else {}),
                    }
                    for binding in self.bindings
                ],
            },
        }
