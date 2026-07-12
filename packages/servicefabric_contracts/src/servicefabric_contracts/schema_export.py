"""Deterministic JSON Schema export for contract snapshots."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from pydantic import BaseModel

from .service_package import ServicePackageDefinition
from .capsules import (
    CapsuleAuthoringManifest,
    CapsuleDefinition,
    CapsuleHostPolicy,
    CapsuleHostRequest,
    CapsuleHostResult,
    CapsuleHostSession,
    CapsuleRevision,
)
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
from .applications import (
    ApplicationArtifactManifest,
    ApplicationBuildRequest,
    ApplicationBuildResult,
    ApplicationDefinition,
    ApplicationRevision,
    SourceBundleManifest,
    StaticWebBuildSpec,
)
from .governance import PolicyDecision, PolicyEvaluationRequest
from .approvals import ApprovalBinding, ApprovalDecision, ApprovalRequest
from .durable_operations import (
    ExecutionAttempt,
    IdempotencyRecord,
    OperationEvent,
    OperationTransition,
    ReconciliationRecord,
)

SCHEMA_ID = "https://schemas.servicefabric.ai/v1alpha1/service-package-definition.schema.json"
SCHEMA_RESOURCES = {
    "service-package-definition.schema.json": (ServicePackageDefinition, SCHEMA_ID, "ServiceFabric ServicePackageDefinition v1alpha1", "ServicePackageDefinition"),
    "capsule-definition.schema.json": (CapsuleDefinition, "https://schemas.servicefabric.ai/v1alpha1/capsule-definition.schema.json", "ServiceFabric CapsuleDefinition v1alpha1", "CapsuleDefinition"),
    "capsule-revision.schema.json": (CapsuleRevision, "https://schemas.servicefabric.ai/v1alpha1/capsule-revision.schema.json", "ServiceFabric CapsuleRevision v1alpha1", "CapsuleRevision"),
    "capsule-authoring-manifest.schema.json": (CapsuleAuthoringManifest, "https://schemas.servicefabric.ai/v1alpha1/capsule-authoring-manifest.schema.json", "ServiceFabric CapsuleAuthoringManifest v1alpha1", "CapsuleAuthoringManifest"),
    "capsule-host-policy.schema.json": (CapsuleHostPolicy, "https://schemas.servicefabric.ai/v1alpha1/capsule-host-policy.schema.json", "ServiceFabric CapsuleHostPolicy v1alpha1", "CapsuleHostPolicy"),
    "capsule-host-request.schema.json": (CapsuleHostRequest, "https://schemas.servicefabric.ai/v1alpha1/capsule-host-request.schema.json", "ServiceFabric CapsuleHostRequest v1alpha1", "CapsuleHostRequest"),
    "capsule-host-session.schema.json": (CapsuleHostSession, "https://schemas.servicefabric.ai/v1alpha1/capsule-host-session.schema.json", "ServiceFabric CapsuleHostSession v1alpha1", "CapsuleHostSession"),
    "capsule-host-result.schema.json": (CapsuleHostResult, "https://schemas.servicefabric.ai/v1alpha1/capsule-host-result.schema.json", "ServiceFabric CapsuleHostResult v1alpha1", "CapsuleHostResult"),
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
    "application-definition.schema.json": (ApplicationDefinition, "https://schemas.servicefabric.ai/v1alpha1/application-definition.schema.json", "ServiceFabric ApplicationDefinition v1alpha1", "ApplicationDefinition"),
    "application-revision.schema.json": (ApplicationRevision, "https://schemas.servicefabric.ai/v1alpha1/application-revision.schema.json", "ServiceFabric ApplicationRevision v1alpha1", "ApplicationRevision"),
    "static-web-build-spec.schema.json": (StaticWebBuildSpec, "https://schemas.servicefabric.ai/v1alpha1/static-web-build-spec.schema.json", "ServiceFabric StaticWebBuildSpec v1alpha1", "StaticWebBuildSpec"),
    "source-bundle-manifest.schema.json": (SourceBundleManifest, "https://schemas.servicefabric.ai/v1alpha1/source-bundle-manifest.schema.json", "ServiceFabric SourceBundleManifest v1alpha1", "SourceBundleManifest"),
    "application-build-request.schema.json": (ApplicationBuildRequest, "https://schemas.servicefabric.ai/v1alpha1/application-build-request.schema.json", "ServiceFabric ApplicationBuildRequest v1alpha1", "ApplicationBuildRequest"),
    "application-build-result.schema.json": (ApplicationBuildResult, "https://schemas.servicefabric.ai/v1alpha1/application-build-result.schema.json", "ServiceFabric ApplicationBuildResult v1alpha1", "ApplicationBuildResult"),
    "application-artifact-manifest.schema.json": (ApplicationArtifactManifest, "https://schemas.servicefabric.ai/v1alpha1/application-artifact-manifest.schema.json", "ServiceFabric ApplicationArtifactManifest v1alpha1", "ApplicationArtifactManifest"),
    "policy-evaluation-request.schema.json": (PolicyEvaluationRequest, "https://schemas.servicefabric.ai/v1alpha1/policy-evaluation-request.schema.json", "ServiceFabric PolicyEvaluationRequest v1alpha1", "PolicyEvaluationRequest"),
    "policy-decision.schema.json": (PolicyDecision, "https://schemas.servicefabric.ai/v1alpha1/policy-decision.schema.json", "ServiceFabric PolicyDecision v1alpha1", "PolicyDecision"),
    "approval-request.schema.json": (ApprovalRequest, "https://schemas.servicefabric.ai/v1alpha1/approval-request.schema.json", "ServiceFabric ApprovalRequest v1alpha1", "ApprovalRequest"),
    "approval-decision.schema.json": (ApprovalDecision, "https://schemas.servicefabric.ai/v1alpha1/approval-decision.schema.json", "ServiceFabric ApprovalDecision v1alpha1", "ApprovalDecision"),
    "approval-binding.schema.json": (ApprovalBinding, "https://schemas.servicefabric.ai/v1alpha1/approval-binding.schema.json", "ServiceFabric ApprovalBinding v1alpha1", "ApprovalBinding"),
    "operation-transition.schema.json": (OperationTransition, "https://schemas.servicefabric.ai/v1alpha1/operation-transition.schema.json", "ServiceFabric OperationTransition v1alpha1", "OperationTransition"),
    "operation-event.schema.json": (OperationEvent, "https://schemas.servicefabric.ai/v1alpha1/operation-event.schema.json", "ServiceFabric OperationEvent v1alpha1", "OperationEvent"),
    "idempotency-record.schema.json": (IdempotencyRecord, "https://schemas.servicefabric.ai/v1alpha1/idempotency-record.schema.json", "ServiceFabric IdempotencyRecord v1alpha1", "IdempotencyRecord"),
    "execution-attempt.schema.json": (ExecutionAttempt, "https://schemas.servicefabric.ai/v1alpha1/execution-attempt.schema.json", "ServiceFabric ExecutionAttempt v1alpha1", "ExecutionAttempt"),
    "reconciliation-record.schema.json": (ReconciliationRecord, "https://schemas.servicefabric.ai/v1alpha1/reconciliation-record.schema.json", "ServiceFabric ReconciliationRecord v1alpha1", "ReconciliationRecord"),
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
