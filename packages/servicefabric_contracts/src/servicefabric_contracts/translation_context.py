"""Explicit information absent from legacy manifests."""
from typing import Literal
from pydantic import Field, field_validator
from .artifacts import ArtifactReference
from .common import ContractModel, Identifier, SEMVER_PATTERN, has_secret_like_key
from .metadata import OwnerReference
from .translation_profiles import TranslationProfile
class TranslationContext(ContractModel):
    source_kind: Literal["template", "catalogue_package", "generated_package", "external_snapshot"]
    package_id: Identifier
    package_version: str = Field(pattern=SEMVER_PATTERN)
    namespace: Identifier | None = None
    owner_ref: OwnerReference
    translation_profile: TranslationProfile
    artifact: ArtifactReference
    parameters: dict[str, str] = Field(default_factory=dict, max_length=16)
    target_environment_classification: Literal["development", "test", "staging", "production_candidate"]
    approved_dependency_refs: tuple[Identifier, ...] = Field(default_factory=tuple, max_length=64)
    review_disposition: Literal["unreviewed", "review_required", "approved_for_authoring"]
    @field_validator("parameters")
    @classmethod
    def safe_parameters(cls, values):
        if set(values) - {"APP_NAME", "APP_SLUG"}: raise ValueError("only known placeholders may be supplied")
        if any(has_secret_like_key(key) for key in values): raise ValueError("context cannot contain credentials")
        return values
