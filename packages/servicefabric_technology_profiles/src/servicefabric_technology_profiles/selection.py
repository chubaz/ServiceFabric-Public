"""Pure selection of reviewed technology-profile governance data.

This package intentionally has no dependency installation, resource provisioning,
or provider-execution entry point.  It records only references already reviewed by
the caller and catalog.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from servicefabric_agent_provider_contracts import ProviderPolicy
from servicefabric_agentic_contracts import ApplicationIntent
from servicefabric_application_factory_contracts import (
    ModuleTechnologySelection,
    TechnologyProfile,
)
from servicefabric_blueprints import ApplicationBlueprint
from servicefabric_framework_kits import FrameworkKitCatalog, get_default_catalog, parse_kit_reference
from servicefabric_framework_kits.errors import KitError


_LIFECYCLE_STATES = frozenset({"development", "build", "runtime"})


class TechnologyProfileSelectionError(ValueError):
    """Raised when a request is not bounded enough for a reviewed decision."""


@dataclass(frozen=True)
class TechnologyProfileRequest:
    """Explicit declarative inputs for one reviewed profile decision.

    ``ApplicationIntent.constraints`` remains input to the decision record only.
    It is never translated into provider arguments, environment values, model
    choices, credentials, or free-form metadata.  Lifecycle, technique-policy,
    resource-question, runtime, and role choices must therefore be supplied by
    their explicit bounded maps.
    """

    profile_id: str
    intent: ApplicationIntent
    blueprint: ApplicationBlueprint
    lifecycle_requirements: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    technique_policy_ids: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    resource_question_ids: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    runtime_family_constraints: Mapping[str, str] = field(default_factory=dict)
    provider_roles: Mapping[str, str] = field(default_factory=dict)


class TechnologyProfileSelector:
    """Select exact catalog kits and return an approval-ready immutable profile."""

    def __init__(
        self,
        provider_policy: ProviderPolicy,
        *,
        catalog: FrameworkKitCatalog | None = None,
    ) -> None:
        self._provider_policy = provider_policy
        self._catalog = catalog or get_default_catalog()

    def select(self, request: TechnologyProfileRequest) -> TechnologyProfile:
        """Return a profile, marking unsupported or open requirements unapproved.

        The method is deterministic and non-executing.  Configuration which
        addresses a module absent from the reviewed blueprint is rejected rather
        than silently ignored.  Problems with a reviewed module become stable
        unmet-requirement identifiers so a factory can reject or escalate them.
        """
        modules = request.blueprint.load_modules(self._catalog)
        module_ids = {module.module_id for module in modules}
        self._reject_unknown_modules(request, module_ids)

        selections: list[ModuleTechnologySelection] = []
        unresolved: set[str] = set()
        for module in modules:
            module_id = module.module_id
            lifecycle = request.lifecycle_requirements.get(module_id, ())
            unknown_lifecycle = set(lifecycle) - _LIFECYCLE_STATES
            if unknown_lifecycle:
                raise TechnologyProfileSelectionError(
                    f"module '{module_id}' has unknown lifecycle requirements: "
                    f"{', '.join(sorted(unknown_lifecycle))}"
                )

            try:
                definition, _adapter = self._catalog.resolve(parse_kit_reference(module.kit))
            except KitError:
                unresolved.add(f"kit-{module_id}")
                continue

            if definition.primitive != module.primitive:
                unresolved.add(f"primitive-{module_id}")
            if not self._supports_lifecycle(definition, lifecycle):
                unresolved.add(f"lifecycle-{module_id}")
            expected_runtime = request.runtime_family_constraints.get(module_id)
            if expected_runtime is not None and expected_runtime != definition.runtime_family:
                unresolved.add(f"runtime-{module_id}")

            resource_ids = tuple(resource.id for resource in module.resources)
            resource_questions = request.resource_question_ids.get(module_id, ())
            unresolved.update(resource_questions)

            role = request.provider_roles.get(module_id, "implementation")
            if not role:
                raise TechnologyProfileSelectionError(
                    f"module '{module_id}' must use a non-empty provider role"
                )
            # Resolve only to validate the role against the frozen policy.  The
            # resolved provider is deliberately not retained in profile data.
            self._provider_policy.provider_for_role(role)

            selections.append(
                ModuleTechnologySelection(
                    module_id=module_id,
                    primitive=module.primitive,
                    kit_reference=(
                        f"{definition.reference.kit_id}@{definition.reference.version}"
                    ),
                    adapter_id=definition.adapter_id,
                    runtime_family=definition.runtime_family,
                    lifecycle_requirements=tuple(lifecycle),
                    technique_policy_ids=tuple(request.technique_policy_ids.get(module_id, ())),
                    resource_requirement_ids=resource_ids,
                    provider_role=role,
                )
            )

        return TechnologyProfile(
            profile_id=request.profile_id,
            application_blueprint_id=request.blueprint.blueprint_id,
            application_blueprint_version=request.blueprint.version,
            module_selections=tuple(selections),
            unresolved_requirements=tuple(sorted(unresolved)),
            approved=not unresolved and len(selections) == len(modules),
        )

    @staticmethod
    def _supports_lifecycle(definition: object, requirements: tuple[str, ...]) -> bool:
        return all(
            {
                "development": definition.development_supported,
                "build": definition.build_supported,
                "runtime": definition.runtime_supported,
            }[state]
            for state in requirements
        )

    @staticmethod
    def _reject_unknown_modules(
        request: TechnologyProfileRequest, module_ids: set[str]
    ) -> None:
        mappings = (
            request.lifecycle_requirements,
            request.technique_policy_ids,
            request.resource_question_ids,
            request.runtime_family_constraints,
            request.provider_roles,
        )
        unknown = sorted({module_id for mapping in mappings for module_id in mapping} - module_ids)
        if unknown:
            raise TechnologyProfileSelectionError(
                f"technology-profile input references unknown blueprint modules: {', '.join(unknown)}"
            )
