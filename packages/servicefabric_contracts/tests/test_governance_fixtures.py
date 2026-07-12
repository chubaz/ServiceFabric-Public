import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from servicefabric_contracts import (
    ApprovalBinding, ApprovalDecision, ApprovalRequest, ExecutionAttempt, IdempotencyRecord,
    OperationEvent, OperationTransition, PolicyDecision, PolicyEvaluationRequest, ReconciliationRecord,
)


FIXTURES = Path(__file__).parent / "fixtures"
CASES = (
    (PolicyEvaluationRequest, "policy_evaluation_request_project_task.json"),
    (PolicyDecision, "policy_decision_project_task.json"),
    (ApprovalRequest, "approval_request_project_task.json"),
    (ApprovalDecision, "approval_decision_project_task.json"),
    (ApprovalBinding, "approval_binding_project_task.json"),
    (OperationTransition, "operation_transition_project_task.json"),
    (OperationEvent, "operation_event_project_task.json"),
    (IdempotencyRecord, "idempotency_record_project_task.json"),
    (ExecutionAttempt, "execution_attempt_project_task.json"),
    (ReconciliationRecord, "reconciliation_record_project_task.json"),
)


class GovernanceFixtureTests(unittest.TestCase):
    def test_fixtures_match_models_and_draft_2020_12_schemas(self) -> None:
        for model, filename in CASES:
            with self.subTest(filename=filename):
                payload = json.loads((FIXTURES / filename).read_text(encoding="utf-8"))
                model.model_validate(payload)
                Draft202012Validator(model.model_json_schema(by_alias=True)).validate(payload)


if __name__ == "__main__":
    unittest.main()
