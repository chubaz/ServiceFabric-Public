import unittest
import json
from datetime import datetime, timezone
from pathlib import Path

from servicefabric_contracts import PolicyEvaluationRequest
from servicefabric_governance import PolicyBundle, PolicyEvaluationError, TrustedPolicyInput, VersionedPolicyEvaluator
D1 = "sha256:" + "1" * 64
FIXTURE = Path(__file__).resolve().parents[2] / "packages" / "servicefabric_contracts" / "tests" / "fixtures" / "policy_evaluation_request_project_task.json"


NOW = datetime(2030, 1, 1, 12, 0, tzinfo=timezone.utc)


def bundle(**overrides):
    values = dict(bundle_id="policy-default", version="1.0.0", digest=D1, allowed_scopes=("project-task-create",), maximum_wall_clock_ms=5000)
    values.update(overrides)
    return PolicyBundle(**values)


def request(**spec_updates):
    payload = json.loads(FIXTURE.read_text(encoding="utf-8")); payload["spec"].update(spec_updates)
    return PolicyEvaluationRequest.model_validate(payload)


def evaluate(policy, value=None):
    value = value or request()
    trusted = TrustedPolicyInput.from_authenticated_adapter(value, adapter_ref="trusted-test-adapter")
    return VersionedPolicyEvaluator((policy,)).evaluate(trusted, now=NOW)


class PolicyEvaluationTests(unittest.TestCase):
    def test_allow_is_deterministic_and_version_bound(self):
        decision1 = evaluate(bundle())
        decision2 = evaluate(bundle())
        self.assertEqual(decision1, decision2)
        self.assertEqual(decision1.spec.outcome, "allow")
        self.assertEqual(decision1.spec.policy_version, "1.0.0")

    def test_deny_overrides_and_grants_no_authority(self):
        decision = evaluate(bundle(denied_effects=("task_create",)))
        self.assertEqual(decision.spec.outcome, "deny")
        self.assertIsNone(decision.spec.effective_authority)
        self.assertEqual(decision.spec.risk, "high")

    def test_require_approval(self):
        decision = evaluate(bundle(approval_effects=("task_create",)))
        self.assertEqual(decision.spec.outcome, "require_approval")
        self.assertEqual(decision.spec.approval_requirement.approval_policy_ref, "approval-default")

    def test_constrained_allow_attenuates_budget(self):
        value = request(requested_budget={"maximum_wall_clock_ms": 9000, "maximum_effect_count": 1})
        decision = evaluate(bundle(maximum_wall_clock_ms=1000), value)
        self.assertEqual(decision.spec.outcome, "constrained_allow")
        self.assertEqual(decision.spec.effective_budget.maximum_wall_clock_ms, 1000)

    def test_missing_authority_denies(self):
        decision = evaluate(bundle(allowed_scopes=()))
        self.assertEqual(decision.spec.outcome, "deny")

    def test_missing_or_changed_policy_fails_closed(self):
        with self.assertRaises(PolicyEvaluationError):
            VersionedPolicyEvaluator(()).evaluate(TrustedPolicyInput.from_authenticated_adapter(request(), adapter_ref="trusted-test"), now=NOW)
        with self.assertRaises(PolicyEvaluationError):
            evaluate(bundle(digest="sha256:" + "f" * 64))

    def test_untrusted_or_anonymous_input_is_rejected(self):
        with self.assertRaises(PolicyEvaluationError): TrustedPolicyInput.from_authenticated_adapter(request(), adapter_ref="caller")
        with self.assertRaises(PolicyEvaluationError): VersionedPolicyEvaluator((bundle(),)).evaluate(request(), now=NOW)


if __name__ == "__main__": unittest.main()
