"""Stable, caller-safe diagnostics for legacy translation."""
from typing import Literal
from pydantic import Field
from .common import ContractModel

DiagnosticSeverity = Literal["info", "warning", "error"]
class TranslationDiagnostic(ContractModel):
    code: str = Field(pattern=r"^(LEGACY|COMPOSITE)_[A-Z0-9_]+$")
    severity: DiagnosticSeverity
    message: str = Field(min_length=1, max_length=1000)
    source_pointer: str = Field(pattern=r"^(/.*)?$")
    canonical_pointer: str | None = Field(default=None, pattern=r"^(/.*)?$")
    remediation: str = Field(min_length=1, max_length=1000)

def diagnostic(code: str, severity: DiagnosticSeverity, message: str, pointer: str, remediation: str, canonical: str | None = None) -> TranslationDiagnostic:
    return TranslationDiagnostic(code=code, severity=severity, message=message, source_pointer=pointer, canonical_pointer=canonical, remediation=remediation)
