"""Local durable-operation domain and persistence adapters."""

from .store import CorruptOperationError, DurableOperationStore, OperationConflictError, StoreLimits
from .state_machine import IllegalTransitionError, LEGAL_TRANSITIONS, OperationStateMachine

__all__ = ["CorruptOperationError", "DurableOperationStore", "IllegalTransitionError", "LEGAL_TRANSITIONS", "OperationConflictError", "OperationStateMachine", "StoreLimits"]
