"""Construct the local governance-operation facade from durable dependencies."""

from __future__ import annotations

from pathlib import Path

from servicefabric_contracts import ApprovalDecision
from servicefabric_governance import ApprovalService, VersionedPolicyEvaluator
from servicefabric_operations import (
    ApprovalConsumptionRepository,
    DeterministicEffectAdapter,
    DurableOperationStore,
    IdempotencyRepository,
    ImmutableRecordRepository,
    ReconciliationService,
)

from .service import GovernanceOperationsService


def create_governance_operations_service(
    *, root: Path, evaluator: VersionedPolicyEvaluator, effect_outcomes: dict[str, str] | None = None
) -> GovernanceOperationsService:
    """Build a local single-process governance facade with durable repositories."""
    audit_records = ImmutableRecordRepository(root / "records")
    consumption = ApprovalConsumptionRepository(root / "approval-consumption")
    approvals = ApprovalService(
        decisions=audit_records.list_by_kind(kind="ApprovalDecision", model=ApprovalDecision),
        consumed_bindings=consumption.consumed(),
        consume_binding=consumption.consume,
    )
    return GovernanceOperationsService(
        evaluator=evaluator,
        approvals=approvals,
        operations=DurableOperationStore(root / "operations"),
        idempotency=IdempotencyRepository(root / "idempotency"),
        reconciliation=ReconciliationService(
            DeterministicEffectAdapter(effect_outcomes or {})
        ),
        audit_records=audit_records,
    )
