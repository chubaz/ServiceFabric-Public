"""Local durable-operation domain and persistence adapters."""

from .store import CorruptOperationError, DurableOperationStore, OperationConflictError, StoreLimits
from .state_machine import IllegalTransitionError, LEGAL_TRANSITIONS, OperationStateMachine
from .idempotency import IdempotencyConflictError, IdempotencyRepository, ReservationResult, idempotency_digest, request_intent_digest
from .attempts import AttemptRepository, CancellationController, RetryDecision, RetryPlanner
from .reconciliation import DeterministicEffectAdapter, ReconciliationResult, ReconciliationService
from .records import ImmutableRecordRepository
from .approval_consumption import ApprovalAlreadyConsumedError, ApprovalConsumptionRepository

__all__ = ["ApprovalAlreadyConsumedError", "ApprovalConsumptionRepository", "AttemptRepository", "CancellationController", "CorruptOperationError", "DeterministicEffectAdapter", "DurableOperationStore", "IdempotencyConflictError", "IdempotencyRepository", "IllegalTransitionError", "ImmutableRecordRepository", "LEGAL_TRANSITIONS", "OperationConflictError", "OperationStateMachine", "ReconciliationResult", "ReconciliationService", "ReservationResult", "RetryDecision", "RetryPlanner", "StoreLimits", "idempotency_digest", "request_intent_digest"]
