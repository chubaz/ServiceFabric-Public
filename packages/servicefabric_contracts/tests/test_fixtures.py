from __future__ import annotations

import json
import unittest
from pathlib import Path

from servicefabric_contracts import (
    CapsuleAuthoringManifest,
    CapsuleDefinition,
    CapsuleHostPolicy,
    CapsuleHostRequest,
    CapsuleHostResult,
    CapsuleHostSession,
    CapsuleRevision,
    ApprovalBinding,
    ApprovalDecision,
    ApprovalRequest,
    EffectReceipt,
    ExecutionAttempt,
    IdempotencyRecord,
    OperationEvent,
    OperationTransition,
    PolicyDecision,
    PolicyEvaluationRequest,
    ReconciliationRecord,
    ServiceFabricOperation,
    ServicePackageDefinition,
    ToolDefinition,
    ToolDeployment,
    ToolInvocationRequest,
    ToolResult,
    ToolRevision,
    ToolStatus,
)

RESOURCE_MODELS = {
    "ServicePackageDefinition": ServicePackageDefinition,
    "CapsuleDefinition": CapsuleDefinition,
    "CapsuleRevision": CapsuleRevision,
    "CapsuleAuthoringManifest": CapsuleAuthoringManifest,
    "CapsuleHostPolicy": CapsuleHostPolicy,
    "CapsuleHostRequest": CapsuleHostRequest,
    "CapsuleHostSession": CapsuleHostSession,
    "CapsuleHostResult": CapsuleHostResult,
    "ToolDefinition": ToolDefinition,
    "ToolRevision": ToolRevision,
    "ToolDeployment": ToolDeployment,
    "ToolStatus": ToolStatus,
    "ToolInvocationRequest": ToolInvocationRequest,
    "ToolResult": ToolResult,
    "EffectReceipt": EffectReceipt,
    "ServiceFabricOperation": ServiceFabricOperation,
    "PolicyEvaluationRequest": PolicyEvaluationRequest,
    "PolicyDecision": PolicyDecision,
    "ApprovalRequest": ApprovalRequest,
    "ApprovalDecision": ApprovalDecision,
    "ApprovalBinding": ApprovalBinding,
    "OperationTransition": OperationTransition,
    "OperationEvent": OperationEvent,
    "IdempotencyRecord": IdempotencyRecord,
    "ExecutionAttempt": ExecutionAttempt,
    "ReconciliationRecord": ReconciliationRecord,
}


class FixtureTests(unittest.TestCase):
    def test_all_representative_fixtures_validate_and_serialize_deterministically(self) -> None:
        fixture_directory = Path(__file__).parent / "fixtures"
        for path in sorted(fixture_directory.glob("*.json")):
            with self.subTest(path=path.name):
                payload = json.loads(path.read_text(encoding="utf-8"))
                model = RESOURCE_MODELS[payload["kind"]].model_validate(payload)
                first = json.dumps(model.model_dump(by_alias=True, mode="json"), sort_keys=True, separators=(",", ":"))
                second = json.dumps(model.model_dump(by_alias=True, mode="json"), sort_keys=True, separators=(",", ":"))
                self.assertEqual(first, second)
