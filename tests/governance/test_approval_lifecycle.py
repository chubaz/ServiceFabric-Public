import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from servicefabric_contracts import PolicyDecision
from servicefabric_contracts.governance import AuthorityGrant
from servicefabric_governance import ApprovalError, ApprovalService, TrustedApprover
from servicefabric_operations import ApprovalConsumptionRepository


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "packages/servicefabric_contracts/tests/fixtures/policy_decision_project_task.json"
NOW = datetime(2030, 1, 1, 12, 1, tzinfo=timezone.utc)
D2 = "sha256:" + "2" * 64
D3 = "sha256:" + "3" * 64


def policy(): return PolicyDecision.model_validate(json.loads(FIXTURE.read_text()))
def approver(): return TrustedApprover.from_authenticated_adapter(subject_ref="approver-bob", authority_ref="approver-authority-1", authentication_strength="multi_factor", adapter_ref="trusted-test")
def authority(): return AuthorityGrant(scopes=("project-task-create",), tenant_ref="tenant-demo", resource_refs=("project-demo",))
def request(service):
    return service.create_request(policy(), request_ref="request-1", operation_ref="operation-1", caller_ref="user-alice", tenant_ref="tenant-demo", argument_digest=D2, effect_class="task-create", requested_authority=authority(), now=NOW, expires_at=NOW + timedelta(minutes=10))


class ApprovalLifecycleTests(unittest.TestCase):
    def test_approved_request_produces_exact_binding(self):
        service=ApprovalService(); req=request(service)
        decision=service.decide(req, approver(), outcome="approved", now=NOW+timedelta(minutes=1), reason_code="approved-reviewed", safe_reason="Approved.")
        binding=service.bind(req, decision, policy_version="1.0.0")
        service.validate_binding(binding, caller_ref="user-alice", revision_ref="1.0.0", intent_digest=D3, argument_digest=D2, now=NOW+timedelta(minutes=2))

    def test_changed_intent_caller_or_revision_is_rejected(self):
        service=ApprovalService(); req=request(service); decision=service.decide(req, approver(), outcome="approved", now=NOW+timedelta(minutes=1), reason_code="approved-reviewed", safe_reason="Approved."); binding=service.bind(req, decision, policy_version="1.0.0")
        for changes in ({"intent_digest":D2},{"caller_ref":"user-mallory"},{"revision_ref":"2.0.0"},{"argument_digest":D3}):
            values=dict(caller_ref="user-alice",revision_ref="1.0.0",intent_digest=D3,argument_digest=D2,now=NOW+timedelta(minutes=2)); values.update(changes)
            with self.assertRaises(ApprovalError): service.validate_binding(binding, **values)

    def test_expiration_and_single_use_are_enforced(self):
        service=ApprovalService(); req=request(service); decision=service.decide(req, approver(), outcome="approved", now=NOW+timedelta(minutes=1), reason_code="approved-reviewed", safe_reason="Approved."); binding=service.bind(req, decision, policy_version="1.0.0")
        args=dict(caller_ref="user-alice", revision_ref="1.0.0", intent_digest=D3, argument_digest=D2)
        with self.assertRaises(ApprovalError): service.validate_binding(binding, now=NOW+timedelta(minutes=11), **args)
        service.validate_binding(binding, now=NOW+timedelta(minutes=2), consume=True, **args)
        with self.assertRaises(ApprovalError): service.validate_binding(binding, now=NOW+timedelta(minutes=3), **args)

    def test_consumption_repository_survives_service_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            repository=ApprovalConsumptionRepository(Path(directory))
            service=ApprovalService(consume_binding=repository.consume)
            req=request(service)
            decision=service.decide(req, approver(), outcome="approved", now=NOW+timedelta(minutes=1), reason_code="approved-reviewed", safe_reason="Approved.")
            binding=service.bind(req, decision, policy_version="1.0.0")
            args=dict(caller_ref="user-alice", revision_ref="1.0.0", intent_digest=D3, argument_digest=D2, now=NOW+timedelta(minutes=2), consume=True)
            service.validate_binding(binding, **args)
            restarted=ApprovalService(consumed_bindings=repository.consumed(), consume_binding=repository.consume)
            with self.assertRaises(ApprovalError): restarted.validate_binding(binding, **args)

    def test_denial_cannot_create_binding(self):
        service=ApprovalService(); req=request(service); decision=service.decide(req, approver(), outcome="denied", now=NOW+timedelta(minutes=1), reason_code="approval-denied", safe_reason="Denied.")
        with self.assertRaises(ApprovalError): service.bind(req, decision, policy_version="1.0.0")

    def test_revocation_is_a_new_immutable_decision(self):
        service=ApprovalService(); req=request(service); decision=service.decide(req, approver(), outcome="approved", now=NOW+timedelta(minutes=1), reason_code="approved-reviewed", safe_reason="Approved.")
        revoked=service.revoke(req, decision, approver(), now=NOW+timedelta(minutes=2), safe_reason="Authority withdrawn.")
        self.assertEqual(revoked.spec.outcome,"revoked"); self.assertEqual(revoked.spec.supersedes_decision_ref,decision.spec.approval_decision_id); self.assertEqual(decision.spec.outcome,"approved")

    def test_untrusted_approver_and_duplicate_decision_are_rejected(self):
        with self.assertRaises(ApprovalError): TrustedApprover.from_authenticated_adapter(subject_ref="x", authority_ref="y", authentication_strength="single_factor", adapter_ref="caller")
        service=ApprovalService(); req=request(service); service.decide(req, approver(), outcome="denied", now=NOW, reason_code="approval-denied", safe_reason="Denied.")
        with self.assertRaises(ApprovalError): service.decide(req, approver(), outcome="denied", now=NOW, reason_code="approval-denied", safe_reason="Denied.")


if __name__=="__main__": unittest.main()
