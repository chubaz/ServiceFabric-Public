from __future__ import annotations

import json
import unittest
from datetime import datetime, timedelta, timezone

from pydantic import ValidationError

from servicefabric_contracts import (
    ApprovalBinding,
    ApprovalDecision,
    ApprovalRequest,
    ExecutionAttempt,
    IdempotencyRecord,
    OperationEvent,
    OperationTransition,
    PolicyDecision,
    PolicyEvaluationRequest,
    ReconciliationRecord,
)


D1 = "sha256:" + "1" * 64
D2 = "sha256:" + "2" * 64
D3 = "sha256:" + "3" * 64
NOW = datetime(2030, 1, 1, 12, 0, tzinfo=timezone.utc)


def metadata(identifier: str) -> dict[str, object]:
    return {
        "id": identifier,
        "name": identifier.replace("-", " ").title(),
        "description": "Deterministic V3 governance fixture.",
        "owner_ref": {"kind": "service", "id": "governance-service"},
    }


def caller() -> dict[str, object]:
    return {
        "subject_ref": "user-alice",
        "principal_type": "human",
        "tenant_ref": "tenant-demo",
        "issuer": "servicefabric-identity",
        "audiences": ["tool-runtime"],
        "scopes": ["project-task-create"],
        "authority_chain_refs": ["authority-chain-1"],
        "authentication_strength": "multi_factor",
    }


def authority() -> dict[str, object]:
    return {"scopes": ["project-task-create"], "tenant_ref": "tenant-demo", "resource_refs": ["project-demo"]}


def approval_scope() -> dict[str, object]:
    return {"effect_refs": ["task-create"], "authority": authority(), "single_use": True}


def resource(kind: str, spec: dict[str, object]) -> dict[str, object]:
    return {"apiVersion": "servicefabric.ai/v1alpha1", "kind": kind, "metadata": metadata(spec[next(iter(spec))]), "spec": spec}


def evaluation_payload() -> dict[str, object]:
    return resource("PolicyEvaluationRequest", {
        "evaluation_request_id": "evaluation-1", "request_ref": "request-1", "request_digest": D1,
        "caller": caller(), "caller_context_digest": D2, "tool_id": "project.create_task",
        "revision_ref": "1.0.0", "operation_ref": "operation-1", "intent_digest": D3,
        "declared_effects": [{"effect_type": "task_create", "target_category": "project-task", "scope": "project-demo", "reversibility": "reversible", "verification_required": True, "approval_required": True, "idempotency_required": True}],
        "required_permissions": [{"permission_id": "project-task-create", "tenant_scope": "caller_tenant", "resource_scope": "project-demo", "delegation_allowed": False}],
        "requested_authority": authority(), "requested_budget": {"maximum_wall_clock_ms": 5000, "maximum_effect_count": 1},
        "risk_hint": "high", "policy_bundle_ref": "policy-default", "policy_version": "1.0.0",
        "policy_digest": D1, "evaluated_at": NOW.isoformat(), "valid_until": (NOW + timedelta(minutes=5)).isoformat(),
    })


def policy_payload() -> dict[str, object]:
    return resource("PolicyDecision", {
        "decision_id": "policy-decision-1", "evaluation_request_ref": "evaluation-1", "evaluation_digest": D1,
        "caller_context_digest": D2, "tool_id": "project.create_task", "revision_ref": "1.0.0", "intent_digest": D3,
        "declared_effect_refs": ["task-create"], "outcome": "require_approval", "risk": "high",
        "policy_bundle_ref": "policy-default", "policy_version": "1.0.0", "policy_digest": D1,
        "effective_authority": authority(), "approval_requirement": {"approval_policy_ref": "approval-high-risk", "effect_refs": ["task-create"], "minimum_approver_strength": "multi_factor"},
        "reason_codes": ["approval-required"], "safe_reason": "High-risk task creation requires approval.",
        "issued_at": NOW.isoformat(), "valid_until": (NOW + timedelta(minutes=5)).isoformat(), "evaluator_ref": "policy-evaluator", "evidence_refs": ["evidence-policy-1"],
    })


def approval_request_payload() -> dict[str, object]:
    return resource("ApprovalRequest", {
        "approval_request_id": "approval-request-1", "policy_decision_ref": "policy-decision-1", "policy_decision_digest": D1,
        "request_ref": "request-1", "operation_ref": "operation-1", "caller_ref": "user-alice", "tenant_ref": "tenant-demo",
        "tool_id": "project.create_task", "revision_ref": "1.0.0", "intent_digest": D3, "argument_digest": D2,
        "effect_class": "task-create", "requested_authority": authority(), "approval_scope": approval_scope(), "risk": "high",
        "reason": "Approve deterministic fixture task creation.", "created_at": NOW.isoformat(), "expires_at": (NOW + timedelta(minutes=10)).isoformat(),
    })


def approval_decision_payload() -> dict[str, object]:
    return resource("ApprovalDecision", {
        "approval_decision_id": "approval-decision-1", "approval_request_ref": "approval-request-1", "approval_request_digest": D1,
        "policy_decision_ref": "policy-decision-1", "intent_digest": D3, "outcome": "approved", "approver_subject_ref": "approver-bob",
        "approver_authority_ref": "approver-authority-1", "decided_at": (NOW + timedelta(minutes=1)).isoformat(),
        "valid_until": (NOW + timedelta(minutes=9)).isoformat(), "reason_code": "approved-reviewed", "safe_reason": "Reviewed and approved.",
        "evidence_refs": ["evidence-approval-1"],
    })


def approval_binding_payload() -> dict[str, object]:
    return resource("ApprovalBinding", {
        "binding_id": "approval-binding-1", "approval_request_ref": "approval-request-1", "approval_decision_ref": "approval-decision-1",
        "approval_decision_digest": D1, "policy_decision_ref": "policy-decision-1", "policy_version": "1.0.0",
        "caller_ref": "user-alice", "tenant_ref": "tenant-demo", "operation_ref": "operation-1", "tool_id": "project.create_task",
        "revision_ref": "1.0.0", "intent_digest": D3, "argument_digest": D2, "effect_class": "task-create",
        "authority_scope": approval_scope(), "valid_from": (NOW + timedelta(minutes=1)).isoformat(), "valid_until": (NOW + timedelta(minutes=9)).isoformat(), "binding_digest": D2,
    })


def transition_payload() -> dict[str, object]:
    return resource("OperationTransition", {
        "transition_id": "transition-2", "operation_ref": "operation-1", "from_state": "accepted", "to_state": "waiting_for_approval",
        "expected_version": 1, "resulting_version": 2, "reason_code": "approval-required", "safe_reason": "Awaiting approval.",
        "transitioned_at": NOW.isoformat(), "actor_ref": "operation-controller", "evidence_refs": ["evidence-policy-1"],
    })


def event_payload() -> dict[str, object]:
    return resource("OperationEvent", {
        "event_id": "event-2", "operation_ref": "operation-1", "sequence": 2, "operation_version": 2, "event_type": "transition",
        "recorded_at": NOW.isoformat(), "previous_event_digest": D1, "event_digest": D2, "transition_ref": "transition-2",
        "evidence_refs": ["evidence-policy-1"], "details": [{"key": "reason", "value": "approval-required"}],
    })


def idempotency_payload() -> dict[str, object]:
    return resource("IdempotencyRecord", {
        "record_id": "idempotency-1", "key_digest": D1, "intent_digest": D3, "scope": "caller", "caller_ref": "user-alice",
        "namespace_ref": "tenant-demo", "request_ref": "request-1", "operation_ref": "operation-1", "state": "in_progress",
        "created_at": NOW.isoformat(), "expires_at": (NOW + timedelta(days=1)).isoformat(),
    })


def attempt_payload() -> dict[str, object]:
    return resource("ExecutionAttempt", {
        "attempt_id": "attempt-1", "operation_ref": "operation-1", "invocation_ref": "invocation-1", "revision_ref": "1.0.0",
        "attempt_number": 1, "state": "started", "started_at": NOW.isoformat(), "retry_eligibility": "not_evaluated", "effect_uncertainty": "none",
    })


def reconciliation_payload() -> dict[str, object]:
    return resource("ReconciliationRecord", {
        "reconciliation_id": "reconciliation-1", "operation_ref": "operation-1", "attempt_ref": "attempt-1",
        "declared_effect_ref": "task-create", "idempotency_digest": D1, "outcome": "known_absent", "verification_method": "fake-provider-query",
        "verified_at": NOW.isoformat(), "evidence_refs": ["evidence-reconciliation-1"], "safe_reason": "Provider confirms no task was created.",
    })


CASES = (
    (PolicyEvaluationRequest, evaluation_payload), (PolicyDecision, policy_payload), (ApprovalRequest, approval_request_payload),
    (ApprovalDecision, approval_decision_payload), (ApprovalBinding, approval_binding_payload), (OperationTransition, transition_payload),
    (OperationEvent, event_payload), (IdempotencyRecord, idempotency_payload), (ExecutionAttempt, attempt_payload),
    (ReconciliationRecord, reconciliation_payload),
)


class GovernanceContractTests(unittest.TestCase):
    def test_all_resources_round_trip(self) -> None:
        for model, factory in CASES:
            with self.subTest(model=model.__name__):
                value = model.model_validate(factory())
                self.assertEqual(value, model.model_validate_json(value.model_dump_json(by_alias=True)))

    def test_all_resources_reject_unknown_fields(self) -> None:
        for model, factory in CASES:
            with self.subTest(model=model.__name__):
                payload = factory(); payload["unexpected"] = True
                with self.assertRaises(ValidationError): model.model_validate(payload)

    def test_timestamps_must_be_timezone_aware(self) -> None:
        payload = evaluation_payload(); payload["spec"]["evaluated_at"] = "2030-01-01T12:00:00"
        with self.assertRaises(ValidationError): PolicyEvaluationRequest.model_validate(payload)

    def test_policy_decision_outcome_invariants(self) -> None:
        payload = policy_payload(); payload["spec"]["approval_requirement"] = None
        with self.assertRaises(ValidationError): PolicyDecision.model_validate(payload)
        payload = policy_payload(); payload["spec"].update(outcome="deny", effective_authority=None, safe_reason=None)
        with self.assertRaises(ValidationError): PolicyDecision.model_validate(payload)

    def test_policy_validity_window(self) -> None:
        payload = policy_payload(); payload["spec"]["valid_until"] = NOW.isoformat()
        with self.assertRaises(ValidationError): PolicyDecision.model_validate(payload)

    def test_approval_request_binds_effect_scope(self) -> None:
        payload = approval_request_payload(); payload["spec"]["effect_class"] = "payment-initiate"
        with self.assertRaises(ValidationError): ApprovalRequest.model_validate(payload)

    def test_approval_decision_consistency(self) -> None:
        payload = approval_decision_payload(); payload["spec"]["valid_until"] = None
        with self.assertRaises(ValidationError): ApprovalDecision.model_validate(payload)
        payload = approval_decision_payload(); payload["spec"].update(outcome="revoked", supersedes_decision_ref=None)
        with self.assertRaises(ValidationError): ApprovalDecision.model_validate(payload)

    def test_binding_rejects_empty_window_and_changed_intent(self) -> None:
        payload = approval_binding_payload(); payload["spec"]["valid_until"] = payload["spec"]["valid_from"]
        with self.assertRaises(ValidationError): ApprovalBinding.model_validate(payload)
        binding = ApprovalBinding.model_validate(approval_binding_payload())
        self.assertFalse(binding.spec.matches_intent(caller_ref="user-mallory", revision_ref="1.0.0", intent_digest=D3, argument_digest=D2))
        self.assertFalse(binding.spec.matches_intent(caller_ref="user-alice", revision_ref="2.0.0", intent_digest=D3, argument_digest=D2))

    def test_transition_versions_are_contiguous(self) -> None:
        payload = transition_payload(); payload["spec"]["resulting_version"] = 4
        with self.assertRaises(ValidationError): OperationTransition.model_validate(payload)

    def test_event_sequence_is_bounded_and_chained(self) -> None:
        payload = event_payload(); payload["spec"]["sequence"] = 0
        with self.assertRaises(ValidationError): OperationEvent.model_validate(payload)
        payload = event_payload(); payload["spec"]["previous_event_digest"] = None
        with self.assertRaises(ValidationError): OperationEvent.model_validate(payload)

    def test_idempotency_never_contains_raw_key(self) -> None:
        payload = idempotency_payload(); payload["spec"]["key"] = "raw-secret-value"
        with self.assertRaises(ValidationError): IdempotencyRecord.model_validate(payload)
        record = IdempotencyRecord.model_validate(idempotency_payload())
        self.assertFalse(record.spec.matches_intent(D2))
        self.assertNotIn("raw-secret-value", record.model_dump_json())

    def test_attempt_terminal_timestamp_and_uncertainty(self) -> None:
        payload = attempt_payload(); payload["spec"]["state"] = "failed"
        with self.assertRaises(ValidationError): ExecutionAttempt.model_validate(payload)
        payload = attempt_payload(); payload["spec"].update(effect_uncertainty="possible", retry_eligibility="eligible")
        with self.assertRaises(ValidationError): ExecutionAttempt.model_validate(payload)

    def test_reconciliation_outcome_consistency(self) -> None:
        payload = reconciliation_payload(); payload["spec"]["verification_method"] = None
        with self.assertRaises(ValidationError): ReconciliationRecord.model_validate(payload)
        payload = reconciliation_payload(); payload["spec"].update(outcome="verification_unavailable", verification_method=None)
        with self.assertRaises(ValidationError): ReconciliationRecord.model_validate(payload)

    def test_schema_generation_is_deterministic(self) -> None:
        for model, _ in CASES:
            self.assertEqual(
                json.dumps(model.model_json_schema(by_alias=True), sort_keys=True),
                json.dumps(model.model_json_schema(by_alias=True), sort_keys=True),
            )


if __name__ == "__main__":
    unittest.main()
