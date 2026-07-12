"""Declarative execution authority budgets."""
from datetime import datetime
from decimal import Decimal
from pydantic import Field, field_validator
from .common import ContractModel

class MonetaryBudget(ContractModel):
    amount: Decimal = Field(ge=0, max_digits=18, decimal_places=6)
    currency: str = Field(pattern=r"^[A-Z]{3}$")

    @field_validator("amount", mode="before")
    @classmethod
    def reject_float(cls, value):
        if isinstance(value, float): raise ValueError("currency must not use floating point")
        return value

class ExecutionBudget(ContractModel):
    deadline: datetime | None = None
    maximum_wall_clock_ms: int | None = Field(default=None, ge=0)
    maximum_provider_calls: int | None = Field(default=None, ge=0)
    maximum_nested_tool_calls: int | None = Field(default=None, ge=0)
    maximum_bytes_in: int | None = Field(default=None, ge=0)
    maximum_bytes_out: int | None = Field(default=None, ge=0)
    maximum_model_tokens: int | None = Field(default=None, ge=0)
    maximum_monetary_cost: MonetaryBudget | None = None
    maximum_evidence_records: int | None = Field(default=None, ge=0)
    maximum_effect_count: int | None = Field(default=None, ge=0)

    @field_validator("deadline")
    @classmethod
    def aware(cls, value):
        if value is not None and (value.tzinfo is None or value.utcoffset() is None): raise ValueError("deadline must be timezone-aware")
        return value
