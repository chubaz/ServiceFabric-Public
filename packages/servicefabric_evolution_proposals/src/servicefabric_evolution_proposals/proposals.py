"""Deterministic proposal construction; this module never applies a proposal."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping
from hashlib import sha256

from servicefabric_distillation_contracts import (
    ApplicationEvidenceBundle,
    BlueprintEvolutionProposal,
    SystemChangeProposal,
)

_BLUEPRINT_CATEGORIES = frozenset(
    {"module", "kit", "resource", "lifecycle", "verification", "guidance"}
)
_SYSTEM_SCOPES = frozenset({"library", "framework-kit", "primitive", "platform"})


class EvolutionProposalError(ValueError):
    """Raised when explicit evidence is insufficient to form a proposal."""


def _identifier(prefix: str, value: str) -> str:
    return f"{prefix}-{sha256(value.encode('utf-8')).hexdigest()[:20]}"


def _evidence_refs(bundle: ApplicationEvidenceBundle, requirement_ref: str) -> tuple[str, ...]:
    refs = {
        requirement_ref,
        *bundle.exact_manifest_refs,
        *bundle.verification_evidence_refs,
        *bundle.review_decision_refs,
        *bundle.documentation_refs,
    }
    return tuple(sorted(ref for ref in refs if ref))


def _validate_category(category: str) -> str:
    if category not in _BLUEPRINT_CATEGORIES:
        raise EvolutionProposalError(f"unsupported blueprint proposal category: {category!r}")
    return category


def propose_blueprint_evolutions(
    bundle: ApplicationEvidenceBundle,
    *,
    blueprint_version: str,
    category_by_requirement: Mapping[str, str] | None = None,
) -> tuple[BlueprintEvolutionProposal, ...]:
    """Return proposal records for the bundle's explicit unmet requirements.

    The caller supplies the exact blueprint version because an evidence bundle
    intentionally identifies a blueprint but does not carry its version.  No
    blueprint is loaded, patched, or otherwise modified.
    """
    if not blueprint_version:
        raise EvolutionProposalError("blueprint_version is required")

    categories = category_by_requirement or {}
    proposals: list[BlueprintEvolutionProposal] = []
    for requirement_ref in sorted(set(bundle.unmet_requirement_refs)):
        category = _validate_category(categories.get(requirement_ref, "guidance"))
        evidence_refs = _evidence_refs(bundle, requirement_ref)
        if not evidence_refs:
            raise EvolutionProposalError(
                f"unmet requirement {requirement_ref!r} has no evidence references"
            )
        proposals.append(
            BlueprintEvolutionProposal(
                proposal_id=_identifier(
                    "blueprint-evolution", f"{bundle.bundle_id}:{requirement_ref}"
                ),
                blueprint_id=bundle.application_blueprint_id,
                blueprint_version=blueprint_version,
                category=category,
                required_behavior=(
                    f"Address the unmet requirement recorded at {requirement_ref}."
                ),
                evidence_refs=evidence_refs,
                proposed_change=(
                    f"Review blueprint {bundle.application_blueprint_id} version "
                    f"{blueprint_version} for {requirement_ref}; this proposal does not "
                    "modify the blueprint."
                ),
                status="proposed",
            )
        )
    return tuple(proposals)


def propose_system_changes(
    bundles: Iterable[ApplicationEvidenceBundle],
    *,
    scope_by_requirement: Mapping[str, str],
    minimum_recurrence: int = 2,
) -> tuple[SystemChangeProposal, ...]:
    """Return system-change records for repeated explicit unmet requirements.

    A scope must be supplied for every emitted requirement.  This prevents the
    builder from inferring a platform change from evidence alone.
    """
    if minimum_recurrence < 1:
        raise EvolutionProposalError("minimum_recurrence must be at least one")

    occurrences: dict[str, list[ApplicationEvidenceBundle]] = defaultdict(list)
    for bundle in bundles:
        for requirement_ref in sorted(set(bundle.unmet_requirement_refs)):
            occurrences[requirement_ref].append(bundle)

    proposals: list[SystemChangeProposal] = []
    for requirement_ref in sorted(occurrences):
        related_bundles = occurrences[requirement_ref]
        if len(related_bundles) < minimum_recurrence:
            continue
        try:
            scope = scope_by_requirement[requirement_ref]
        except KeyError as error:
            raise EvolutionProposalError(
                f"a proposed system change requires an explicit scope for {requirement_ref!r}"
            ) from error
        if scope not in _SYSTEM_SCOPES:
            raise EvolutionProposalError(f"unsupported system proposal scope: {scope!r}")

        evidence_refs = tuple(
            sorted(
                {
                    ref
                    for bundle in related_bundles
                    for ref in _evidence_refs(bundle, requirement_ref)
                }
            )
        )
        proposals.append(
            SystemChangeProposal(
                proposal_id=_identifier("system-change", requirement_ref),
                source_requirement_ref=requirement_ref,
                proposed_scope=scope,
                required_behavior=(
                    f"Address the repeatedly unmet requirement recorded at {requirement_ref}."
                ),
                recurrence_count=len(related_bundles),
                affected_applications=tuple(
                    sorted({bundle.application_id for bundle in related_bundles})
                ),
                evidence_refs=evidence_refs,
                urgency="normal",
                status="proposed",
            )
        )
    return tuple(proposals)
