"""Construct the local governance-operation facade from durable dependencies."""

from __future__ import annotations

from pathlib import Path

from servicefabric_governance import ApprovalService, VersionedPolicyEvaluator
from servicefabric_operations import (
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
    return GovernanceOperationsService(
        evaluator=evaluator,
        approvals=ApprovalService(),
        operations=DurableOperationStore(root / "operations"),
        idempotency=IdempotencyRepository(root / "idempotency"),
        reconciliation=ReconciliationService(
            DeterministicEffectAdapter(effect_outcomes or {})
        ),
        audit_records=ImmutableRecordRepository(root / "records"),
    )
