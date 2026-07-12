from datetime import datetime
from typing import Literal
from pydantic import Field
from .common import ContractModel, Identifier
class ObservedEffect(ContractModel):
    effect_id: Identifier
    declared_effect_ref: Identifier
    effect_type: Identifier
    target_ref: Identifier
    provider_operation_ref: Identifier | None = None
    state: Literal["attempted", "committed", "verified", "reconciled", "reversed", "failed", "unknown"]
    observed_at: datetime
    before_ref: Identifier | None = None
    after_ref: Identifier | None = None
    reversibility: Literal["reversible", "irreversible", "unknown"]
