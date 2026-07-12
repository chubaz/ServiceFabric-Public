from datetime import datetime
from typing import Literal
from pydantic import Field, field_validator
from .common import ContractModel, Digest, Identifier
class EvidenceRecord(ContractModel):
    evidence_id: Identifier
    evidence_type: Literal["document", "web_resource", "database_record", "provider_response", "calculation", "log_reference", "human_confirmation", "artifact"]
    source_ref: Identifier
    locator: str = Field(min_length=1, max_length=512)
    content_digest: Digest | None = None
    collected_at: datetime
    trust_classification: Literal["untrusted", "external", "verified", "platform"]
    claims: tuple[str, ...] = Field(default_factory=tuple, max_length=32)
    summary: str = Field(min_length=1, max_length=2000)
    provenance_refs: tuple[Identifier, ...] = Field(default_factory=tuple, max_length=32)
    @field_validator("locator")
    @classmethod
    def no_credentials(cls, value):
        lowered=value.lower()
        if "@" in value and "://" in value or any(x in lowered for x in ("token=", "api_key=", "apikey=", "authorization=")):
            raise ValueError("evidence locators cannot contain credentials")
        return value
    @field_validator("collected_at")
    @classmethod
    def aware(cls, value):
        if value.tzinfo is None or value.utcoffset() is None: raise ValueError("evidence timestamps must be timezone-aware")
        return value
