"""Deterministic migration report; not deployment readiness."""
from typing import Literal
from pydantic import Field, model_validator
from .common import ContractModel, Digest
from .service_package import ServicePackageDefinition
from .translation_diagnostics import TranslationDiagnostic
from .translation_profiles import TranslationProfile
class TranslationSource(ContractModel):
    kind: Literal["template", "catalogue_package", "generated_package", "external_snapshot", "unknown"]
    reference: str = Field(min_length=1, max_length=512)
class LegacyManifestTranslationReport(ContractModel):
    api_version: Literal["servicefabric.ai/v1alpha1"] = Field(alias="apiVersion")
    kind: Literal["LegacyManifestTranslationReport"]
    status: Literal["translated", "translated_with_warnings", "requires_context", "requires_split", "unsupported", "invalid", "unsafe"]
    source: TranslationSource
    source_digest: Digest
    profile: TranslationProfile
    canonical_resource: ServicePackageDefinition | None = None
    diagnostics: tuple[TranslationDiagnostic, ...] = Field(default_factory=tuple)
    mapped_fields: tuple[str, ...] = Field(default_factory=tuple)
    unmapped_fields: tuple[str, ...] = Field(default_factory=tuple)
    discarded_fields: tuple[str, ...] = Field(default_factory=tuple)
    required_context: tuple[str, ...] = Field(default_factory=tuple)
    assumptions: tuple[str, ...] = Field(default_factory=tuple)
    requires_human_review: bool = True
    translation_version: Literal["0.4.0a1"] = "0.4.0a1"
    canonical_resource_digest: Digest | None = None
    model_config = ContractModel.model_config | {"populate_by_name": True}
    @model_validator(mode="after")
    def consistency(self):
        errors=any(item.severity == "error" for item in self.diagnostics)
        if self.status in {"translated", "translated_with_warnings"} and self.canonical_resource is None: raise ValueError("translated reports require a canonical resource")
        if errors and self.canonical_resource is not None: raise ValueError("error diagnostics prohibit canonical output")
        return self
