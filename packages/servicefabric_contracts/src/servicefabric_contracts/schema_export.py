"""Deterministic JSON Schema export for contract snapshots."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from pydantic import BaseModel

from .service_package import ServicePackageDefinition
from .tool_definition import ToolDefinition
from .tool_deployment import ToolDeployment
from .tool_revision import ToolRevision
from .tool_status import ToolStatus
from .effect_receipt import EffectReceipt
from .errors import ToolError
from .evidence import EvidenceRecord
from .invocation import ToolInvocationAcceptance, ToolInvocationRequest
from .operations import ServiceFabricOperation
from .results import ToolResult
from .version import __version__
from .translation_report import LegacyManifestTranslationReport
from .toolset import ToolsetDefinition

SCHEMA_ID = "https://schemas.servicefabric.ai/v1alpha1/service-package-definition.schema.json"
SCHEMA_RESOURCES = {
    "service-package-definition.schema.json": (ServicePackageDefinition, SCHEMA_ID, "ServiceFabric ServicePackageDefinition v1alpha1", "ServicePackageDefinition"),
    "tool-definition.schema.json": (ToolDefinition, "https://schemas.servicefabric.ai/v1alpha1/tool-definition.schema.json", "ServiceFabric ToolDefinition v1alpha1", "ToolDefinition"),
    "tool-revision.schema.json": (ToolRevision, "https://schemas.servicefabric.ai/v1alpha1/tool-revision.schema.json", "ServiceFabric ToolRevision v1alpha1", "ToolRevision"),
    "tool-deployment.schema.json": (ToolDeployment, "https://schemas.servicefabric.ai/v1alpha1/tool-deployment.schema.json", "ServiceFabric ToolDeployment v1alpha1", "ToolDeployment"),
    "tool-status.schema.json": (ToolStatus, "https://schemas.servicefabric.ai/v1alpha1/tool-status.schema.json", "ServiceFabric ToolStatus v1alpha1", "ToolStatus"),
    "tool-invocation-request.schema.json": (ToolInvocationRequest, "https://schemas.servicefabric.ai/v1alpha1/tool-invocation-request.schema.json", "ServiceFabric ToolInvocationRequest v1alpha1", "ToolInvocationRequest"),
    "tool-invocation-acceptance.schema.json": (ToolInvocationAcceptance, "https://schemas.servicefabric.ai/v1alpha1/tool-invocation-acceptance.schema.json", "ServiceFabric ToolInvocationAcceptance v1alpha1", "ToolInvocationAcceptance"),
    "tool-result.schema.json": (ToolResult, "https://schemas.servicefabric.ai/v1alpha1/tool-result.schema.json", "ServiceFabric ToolResult v1alpha1", "ToolResult"),
    "tool-error.schema.json": (ToolError, "https://schemas.servicefabric.ai/v1alpha1/tool-error.schema.json", "ServiceFabric ToolError v1alpha1", "ToolError"),
    "evidence-record.schema.json": (EvidenceRecord, "https://schemas.servicefabric.ai/v1alpha1/evidence-record.schema.json", "ServiceFabric EvidenceRecord v1alpha1", "EvidenceRecord"),
    "effect-receipt.schema.json": (EffectReceipt, "https://schemas.servicefabric.ai/v1alpha1/effect-receipt.schema.json", "ServiceFabric EffectReceipt v1alpha1", "EffectReceipt"),
    "servicefabric-operation.schema.json": (ServiceFabricOperation, "https://schemas.servicefabric.ai/v1alpha1/servicefabric-operation.schema.json", "ServiceFabric Operation v1alpha1", "ServiceFabricOperation"),
    "legacy-manifest-translation-report.schema.json": (LegacyManifestTranslationReport, "https://schemas.servicefabric.ai/v1alpha1/legacy-manifest-translation-report.schema.json", "ServiceFabric Legacy Manifest Translation Report v1alpha1", "LegacyManifestTranslationReport"),
    "toolset-definition.schema.json": (ToolsetDefinition, "https://schemas.servicefabric.ai/v1alpha1/toolset-definition.schema.json", "ServiceFabric ToolsetDefinition v1alpha1", "ToolsetDefinition"),
}


def canonical_json(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def service_package_schema() -> dict[str, object]:
    return resource_schema(ServicePackageDefinition, SCHEMA_ID, "ServiceFabric ServicePackageDefinition v1alpha1")


def resource_schema(model: type[BaseModel], schema_id: str, title: str) -> dict[str, object]:
    schema = model.model_json_schema(by_alias=True)
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = schema_id
    schema["title"] = title
    return schema


def write_schema_snapshot(output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    index_entries: list[dict[str, str]] = []
    for filename, (model, schema_id, title, kind) in SCHEMA_RESOURCES.items():
        schema_path = output_dir / filename
        content = canonical_json(resource_schema(model, schema_id, title))
        schema_path.write_text(content, encoding="utf-8")
        index_entries.append(
            {
                "kind": kind,
                "schema_id": schema_id,
                "schema_path": filename,
                "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
            }
        )
    index = {
        "api_version": "servicefabric.ai/v1alpha1",
        "contract_package_version": __version__,
        "schemas": sorted(index_entries, key=lambda entry: entry["kind"]),
    }
    (output_dir / "schema-index.json").write_text(canonical_json(index), encoding="utf-8")
    return output_dir / "service-package-definition.schema.json"
