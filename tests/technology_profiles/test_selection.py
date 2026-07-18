from __future__ import annotations

import unittest

from servicefabric_agent_provider_contracts import ProviderPolicy
from servicefabric_agentic_contracts import ApplicationIntent
from servicefabric_blueprints import ApplicationBlueprint, BlueprintModule
from servicefabric_technology_profiles import (
    TechnologyProfileRequest,
    TechnologyProfileSelector,
    TechnologyProfileSelectionError,
)


def blueprint(*, primitive: str = "service", kit: str = "fastapi-service") -> ApplicationBlueprint:
    return ApplicationBlueprint(
        blueprint_id="sample-blueprint",
        version="1.0.0",
        title="Sample",
        description="A reviewed test blueprint.",
        modules=(
            BlueprintModule.from_manifest(
                {
                    "apiVersion": "servicefabric.local/v1",
                    "kind": "ApplicationModule",
                    "metadata": {"id": "api", "version": "1.0.0"},
                    "spec": {
                        "primitive": primitive,
                        "kit": f"{kit} @ServiceFabric/examples.{kit}-1.0.0.json",
                        "source": "api",
                        "requires": {"resources": [{"id": "database", "type": "database"}]},
                    },
                }
            ),
        ),
    )


def request(**changes: object) -> TechnologyProfileRequest:
    values: dict[str, object] = {
        "profile_id": "profile-sample",
        "intent": ApplicationIntent(
            intent_id="intent-sample",
            mode="create",
            objective="Create a sample API",
            constraints=("runtime-family:python",),
            requested_capabilities=("http-api",),
        ),
        "blueprint": blueprint(),
        "lifecycle_requirements": {"api": ("development", "build", "runtime")},
        "technique_policy_ids": {"api": ("technique-api-v1",)},
        "provider_roles": {"api": "implementation"},
    }
    values.update(changes)
    return TechnologyProfileRequest(**values)


class TechnologyProfileSelectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.selector = TechnologyProfileSelector(
            ProviderPolicy(
                default_provider="codex",
                role_overrides={"implementation": "codex"},
                maximum_parallel_per_provider=1,
                timeout_seconds=60,
            )
        )

    def test_selects_exact_reviewed_kit_without_provider_configuration(self) -> None:
        profile = self.selector.select(request())

        self.assertTrue(profile.approved)
        self.assertEqual(profile.module_selections[0].kit_reference, "fastapi-service@1.0.0")
        self.assertEqual(profile.module_selections[0].adapter_id, "reviewed-fastapi-v1")
        self.assertEqual(profile.module_selections[0].runtime_family, "python")
        self.assertEqual(profile.module_selections[0].resource_requirement_ids, ("database",))
        self.assertEqual(profile.module_selections[0].provider_role, "implementation")
        self.assertFalse(hasattr(profile.module_selections[0], "provider_id"))

    def test_unsupported_lifecycle_and_resource_question_leave_profile_unapproved(self) -> None:
        profile = self.selector.select(
            request(
                blueprint=blueprint(primitive="library", kit="python-library"),
                lifecycle_requirements={"api": ("development", "build", "runtime")},
                resource_question_ids={"api": ("resource-database-compatibility",)},
            )
        )

        self.assertFalse(profile.approved)
        self.assertEqual(
            profile.unresolved_requirements,
            ("lifecycle-api", "resource-database-compatibility"),
        )

    def test_runtime_constraint_mismatch_is_unapproved(self) -> None:
        profile = self.selector.select(
            request(runtime_family_constraints={"api": "node"})
        )

        self.assertFalse(profile.approved)
        self.assertEqual(profile.unresolved_requirements, ("runtime-api",))

    def test_unknown_module_input_is_rejected(self) -> None:
        with self.assertRaisesRegex(TechnologyProfileSelectionError, "unknown blueprint modules"):
            self.selector.select(request(provider_roles={"other": "implementation"}))

    def test_unknown_lifecycle_is_rejected(self) -> None:
        with self.assertRaisesRegex(TechnologyProfileSelectionError, "unknown lifecycle"):
            self.selector.select(request(lifecycle_requirements={"api": ("deploy",)}))
