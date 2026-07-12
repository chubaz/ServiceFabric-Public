"""Deterministic JSON Schema export for contract snapshots."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .service_package import ServicePackageDefinition
from .version import __version__

SCHEMA_ID = "https://schemas.servicefabric.ai/v1alpha1/service-package-definition.schema.json"


def canonical_json(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def service_package_schema() -> dict[str, object]:
    schema = ServicePackageDefinition.model_json_schema(by_alias=True)
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = SCHEMA_ID
    schema["title"] = "ServiceFabric ServicePackageDefinition v1alpha1"
    return schema


def write_schema_snapshot(output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    schema_path = output_dir / "service-package-definition.schema.json"
    content = canonical_json(service_package_schema())
    schema_path.write_text(content, encoding="utf-8")
    index = {
        "api_version": "servicefabric.ai/v1alpha1",
        "contract_package_version": __version__,
        "kind": "ServicePackageDefinition",
        "schema_id": SCHEMA_ID,
        "schema_path": schema_path.name,
        "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
    }
    (output_dir / "schema-index.json").write_text(canonical_json(index), encoding="utf-8")
    return schema_path
