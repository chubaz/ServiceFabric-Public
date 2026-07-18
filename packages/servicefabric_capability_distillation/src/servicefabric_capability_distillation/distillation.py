"""Create proposed capability records from explicit declarations only.

This module deliberately has no filesystem, route-discovery, registry, or
publication dependency.  Its caller supplies the bounded evidence bundle and
the already-declared operation and capability records to consider.
"""

from __future__ import annotations

from dataclasses import dataclass

from servicefabric_capability_model import CapabilityDefinition
from servicefabric_distillation_contracts import ApplicationEvidenceBundle, CapabilityCandidate
from servicefabric_operation_model import OperationDefinition


class CapabilityDistillationError(ValueError):
    """Raised when supplied declarations are outside the evidence boundary."""


@dataclass(frozen=True)
class CapabilityDistillationRequest:
    """Caller-owned inputs for one bounded capability-distillation run."""

    evidence_bundle: ApplicationEvidenceBundle
    declared_operations: tuple[OperationDefinition, ...]
    declared_capabilities: tuple[CapabilityDefinition, ...]
    evidence_refs: tuple[str, ...] = ()


def distill_capability_candidates(request: CapabilityDistillationRequest) -> tuple[CapabilityCandidate, ...]:
    """Return deterministic proposed records for reviewed, declared capabilities.

    Every candidate must point to an operation named by the evidence bundle.
    Optional explicit evidence references are accepted only when they are
    already named by that bundle.  A candidate is merely ``proposed``: this
    function cannot approve or publish it.
    """

    bundle = request.evidence_bundle
    operations = _operations_by_id(request.declared_operations, bundle.application_id)
    allowed_evidence = _allowed_evidence_refs(bundle)
    evidence_refs = _candidate_evidence_refs(bundle, request.evidence_refs, allowed_evidence)
    capability_refs = set(bundle.capability_refs)
    candidates: list[CapabilityCandidate] = []

    for definition in sorted(request.declared_capabilities, key=lambda value: value.metadata.id):
        capability_id = definition.metadata.id
        operation_ref = definition.spec.operation_ref
        if operation_ref not in operations:
            raise CapabilityDistillationError(
                f"capability '{capability_id}' references undeclared operation '{operation_ref}'"
            )
        if operation_ref not in bundle.operation_refs:
            raise CapabilityDistillationError(
                f"operation '{operation_ref}' is not named by evidence bundle '{bundle.bundle_id}'"
            )
        if capability_refs and capability_id not in capability_refs:
            raise CapabilityDistillationError(
                f"capability '{capability_id}' is not named by evidence bundle '{bundle.bundle_id}'"
            )
        candidates.append(CapabilityCandidate(
            candidate_id=f"capability-candidate.{bundle.bundle_id}.{capability_id}",
            application_id=bundle.application_id,
            operation_ref=operation_ref,
            proposed_definition=definition,
            evidence_refs=evidence_refs,
            rationale=(
                "The capability and its operation are explicit declarations named by "
                f"evidence bundle '{bundle.bundle_id}'."
            ),
            confidence=1.0,
            status="proposed",
        ))
    return tuple(candidates)


def _operations_by_id(
    operations: tuple[OperationDefinition, ...], application_id: str
) -> dict[str, OperationDefinition]:
    result: dict[str, OperationDefinition] = {}
    for operation in operations:
        if operation.application_ref != application_id:
            raise CapabilityDistillationError(
                f"operation '{operation.operation_id}' belongs to '{operation.application_ref}', "
                f"not '{application_id}'"
            )
        if operation.operation_id in result:
            raise CapabilityDistillationError(f"operation '{operation.operation_id}' was supplied more than once")
        result[operation.operation_id] = operation
    return result


def _allowed_evidence_refs(bundle: ApplicationEvidenceBundle) -> set[str]:
    return {
        *bundle.exact_manifest_refs,
        *bundle.verification_evidence_refs,
        *bundle.review_decision_refs,
        *bundle.documentation_refs,
        *bundle.content_digests,
    }


def _candidate_evidence_refs(
    bundle: ApplicationEvidenceBundle,
    supplied_refs: tuple[str, ...],
    allowed_refs: set[str],
) -> tuple[str, ...]:
    if len(set(supplied_refs)) != len(supplied_refs):
        raise CapabilityDistillationError("evidence_refs must be unique")
    unknown = set(supplied_refs) - allowed_refs
    if unknown:
        raise CapabilityDistillationError(
            f"evidence references are not named by bundle '{bundle.bundle_id}': {', '.join(sorted(unknown))}"
        )
    return (f"bundle:{bundle.bundle_id}", *sorted(supplied_refs))
