"""Bounded parser for the advisory legacy manifest format."""
from __future__ import annotations
import json, re
from pydantic import Field, field_validator
from .common import ContractModel, has_secret_like_key

MAX_MANIFEST_BYTES = 128 * 1024
PLACEHOLDER_RE = re.compile(r"\{\{([^{}]+)\}\}")
class DuplicateJsonKey(ValueError): pass
class LegacyRules(ContractModel):
    compilation: tuple[str, ...] = Field(default_factory=tuple, max_length=64)
    execution: tuple[str, ...] = Field(default_factory=tuple, max_length=64)
    avoid: tuple[str, ...] = Field(default_factory=tuple, max_length=64)
class LegacyManifest(ContractModel):
    app_name: str = Field(min_length=1, max_length=200)
    app_slug: str = Field(min_length=1, max_length=128)
    template: str = Field(min_length=1, max_length=128)
    description: str = Field(min_length=1, max_length=4000)
    core_services: dict[str, str] = Field(default_factory=dict, max_length=64)
    rules: LegacyRules
    @field_validator("core_services")
    @classmethod
    def safe_keys(cls, values):
        if any(has_secret_like_key(key) for key in values): raise ValueError("secret-like legacy fields are unsafe")
        return values

def _pairs(pairs):
    result={}
    for key,value in pairs:
        if key in result: raise DuplicateJsonKey(key)
        result[key]=value
    return result
def parse_legacy_manifest(source: bytes) -> LegacyManifest:
    if len(source) > MAX_MANIFEST_BYTES: raise ValueError("legacy manifest exceeds size limit")
    raw=json.loads(source.decode("utf-8"), object_pairs_hook=_pairs)
    return LegacyManifest.model_validate(raw)
def placeholders(manifest: LegacyManifest) -> tuple[str, ...]:
    values=(manifest.app_name, manifest.app_slug, manifest.template, manifest.description)
    return tuple(sorted({match.group(1) for value in values for match in PLACEHOLDER_RE.finditer(value)}))
