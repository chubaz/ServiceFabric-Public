from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from servicefabric_agentic_contracts import (
    AgentHandoff,
    AgentRunPlan,
    AgentTask,
    AgentTaskResult,
    ApplicationIntent,
    VerificationEvidence,
)
from servicefabric_application_factory_contracts import (
    ApplicationFactoryHandoff,
    EngineeringBlueprint,
    EngineeringLane,
    ModuleTechnologySelection,
    TechnologyProfile,
    UnmetRequirement,
)
from servicefabric_capability_model import (
    CapabilityDefinition,
    CapabilityDefinitionSpec,
    CapabilityMetadata,
)
from servicefabric_capability_registry import CapabilityRegistry
from servicefabric_contracts.effects import EffectContract, EffectDeclaration
from servicefabric_distillation_contracts import DistillationDecision, TechniquePolicyDefinition
from servicefabric_engineering_distillation import EngineeringPatternCatalog
from servicefabric_operation_model import HttpBinding, OperationDefinition
from servicefabric_technique_policies import TechniquePolicyCatalog

from servicefabric_client.distillation import (
    DistillationError,
    DistillationInputs,
    DistillationService,
    FileDistillationDecisionStore,
    ManifestSource,
)
from servicefabric_client.main import parser


class _Factory:
    def __init__(self, repository: Path) -> None:
        intent = ApplicationIntent(
            intent_id="notes", mode="create", objective="Create notes", application_id="notes"
        )
        self.plan = AgentRunPlan(
            run_id="run-notes",
            intent=intent,
            tasks=(AgentTask(
                task_id="implementation", role="implementation", objective="Implement notes",
                allowed_paths=("src",), verification_commands=("python3 -m unittest",),
            ),),
            maximum_parallel_tasks=1,
        )
        result = AgentTaskResult(
            task_id="implementation", status="success", changed_paths=("src/app.py",),
            commit_sha="abcdef0",
            evidence=(VerificationEvidence(
                command="python3 -m unittest", exit_code=0, summary="passed",
                artifact_ref="verification:unit",
            ),),
        )
        unmet = UnmetRequirement(
            requirement_id="unmet-database", application_id="notes", run_id="run-notes",
            required_behavior="Provide a reviewed database binding.",
            evidence_refs=("requirement-evidence:database",), proposed_scope="platform", urgency="high",
        )
        profile = TechnologyProfile(
            profile_id="profile-notes", application_blueprint_id="notes-blueprint",
            application_blueprint_version="1.0.0", approved=True,
            module_selections=(ModuleTechnologySelection(
                module_id="api", primitive="http", kit_reference="fastapi-service@1.0.0",
                adapter_id="fastapi-service", runtime_family="python",
                technique_policy_ids=("python.web",), provider_role="implementation",
            ),),
        )
        lane = EngineeringLane(
            lane_id="implementation", role="implementation", module_ids=("api",),
            allowed_paths=("src",), verification_commands=("python3 -m unittest",),
            provider_role="implementation",
        )
        engineering = EngineeringBlueprint(
            blueprint_id="engineering-notes", application_id="notes",
            application_blueprint_id="notes-blueprint", technology_profile_id="profile-notes",
            agent_run_plan=self.plan, lanes=(lane,), integration_lane_id="implementation",
            acceptance_lane_id="implementation", maximum_parallel_tasks=1,
        )
        handoff = ApplicationFactoryHandoff(
            run_id="run-notes", application_id="notes", status="success",
            integration_commit="abcdef0", agent_handoff_ref="agent:run-notes",
            review_decision_refs=("review:accepted",), unmet_requirements=(unmet,),
            verification_evidence=("provider-usage:run-notes",),
        )
        self.value = {
            "run_id": "run-notes", "application_id": "notes",
            "repository_root": str(repository), "repository_head": "abcdef0",
            "application_blueprint_id": "notes-blueprint",
            "application_blueprint_version": "1.0.0",
            "technology_profile": profile, "engineering_blueprint": engineering,
            "agent_run_plan": self.plan, "agent_task_results": (result,),
            "agent_handoff": AgentHandoff(
                run_id="run-notes", status="success", task_results=(result,)
            ),
            "reviews": (), "unmet_requirements": (unmet,), "factory_handoff": handoff,
        }

    def distillation_inputs(self, run_id: str) -> dict[str, object]:
        if run_id != "run-notes":
            raise ValueError("unknown run")
        return self.value


class DistillationCompositionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        (self.root / "src").mkdir()
        (self.root / "src/app.py").write_text("VALUE = 1\n", encoding="utf-8")
        (self.root / "application.json").write_text('{"id":"notes"}\n', encoding="utf-8")
        state = self.root / "state"
        self.service = DistillationService(
            _Factory(self.root), CapabilityRegistry(state / "capabilities"),
            TechniquePolicyCatalog(state / "techniques"),
            EngineeringPatternCatalog(state / "patterns"),
            FileDistillationDecisionStore(state / "decisions"),
        )
        operation = OperationDefinition(
            operation_id="notes.search", version="1.0.0", application_ref="notes",
            module_ref="api", interface_ref="api",
            bindings=(HttpBinding("notes-search", "GET", "/notes"),),
        )
        capability = CapabilityDefinition(
            api_version="servicefabric.local/v1", kind="CapabilityDefinition",
            metadata=CapabilityMetadata(id="notes.search", title="Search notes", domain="notes"),
            spec=CapabilityDefinitionSpec(
                operation_ref="notes.search", objective="Search reviewed notes",
                capability_class="retrieval", concepts=("notes",), expected_inputs=("query",),
                expected_outputs=("matches",), effect_contract=EffectContract(effects=(
                    EffectDeclaration(
                        effect_type="external_read", target_category="notes", scope="notes",
                        reversibility="not_applicable", verification_required=False,
                        approval_required=False, idempotency_required=False,
                    ),
                )),
            ),
        )
        policy = TechniquePolicyDefinition(
            policy_id="python.web", version="1.0.0",
            applicable_kit_refs=("fastapi-service@1.0.0",),
            approved_techniques=("dependency-injection",),
        )
        self.inputs = DistillationInputs(
            run_id="run-notes",
            manifests=(ManifestSource(
                ref="manifest:notes", path="application.json", source_paths=("src",),
                operation_refs=("notes.search",), capability_refs=("notes.search",),
                documentation_refs=("docs:notes",),
            ),),
            declared_operations=(operation,), declared_capabilities=(capability,),
            technique_policy_definitions=(policy,),
            blueprint_categories={"unmet-database": "resource"},
            system_scopes={"unmet-database": "platform"},
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_collect_is_exact_manifest_bounded_and_rejects_recursive_sources(self) -> None:
        bundle = self.service.collect(self.inputs).bundle
        self.assertEqual(bundle.exact_manifest_refs, ("manifest:notes",))
        self.assertEqual(bundle.changed_path_refs, ("src/app.py",))
        self.assertEqual(bundle.unmet_requirement_refs, ("unmet-database",))
        invalid = DistillationInputs(**{
            **self.inputs.__dict__,
            "manifests": (ManifestSource(ref="manifest:all", path="src"),),
        })
        with self.assertRaisesRegex(DistillationError, "exact regular file"):
            self.service.collect(invalid)

    def test_analyze_returns_candidates_in_type_then_identity_order(self) -> None:
        analysis = self.service.analyze(self.inputs)
        identities = [
            getattr(item, "candidate_id", getattr(item, "proposal_id", None))
            for item in analysis.candidates
        ]
        self.assertEqual(len(identities), 5)
        self.assertEqual(identities[0], "capability-candidate.evidence-run-notes.notes.search")
        self.assertEqual(analysis.blueprint_proposals[0].status, "proposed")
        self.assertEqual(analysis.system_proposals[0].status, "proposed")

    def test_decisions_are_immutable_and_publication_is_approved_only_and_idempotent(self) -> None:
        analysis = self.service.analyze(self.inputs)
        for candidate in analysis.candidates:
            identity = getattr(candidate, "candidate_id", getattr(candidate, "proposal_id", ""))
            approve = identity.startswith(("capability-", "technique-", "engineering-"))
            self.service.decide(DistillationDecision(
                decision_id=f"decision.{identity}", candidate_ref=identity,
                decision="approve" if approve else "reject", reason="Reviewed evidence.",
                decided_by="reviewer",
            ))
        first = self.service.report(self.inputs)
        second = self.service.report(self.inputs)
        self.assertEqual(first, second)
        self.assertEqual(
            tuple(ref.split(":", 1)[0] for ref in first.published_references),
            ("capability", "engineering-pattern", "technique-policy"),
        )
        self.assertEqual(len(first.blueprint_proposals), 1)
        self.assertEqual(len(first.system_proposals), 1)
        conflicting = DistillationDecision(
            decision_id=f"decision.{analysis.candidates[0].candidate_id}",
            candidate_ref=analysis.candidates[0].candidate_id, decision="reject",
            reason="Different.", decided_by="reviewer",
        )
        with self.assertRaisesRegex(DistillationError, "immutable decision|already immutable"):
            self.service.decide(conflicting)

    def test_final_cli_exposes_distillation_lifecycle_and_foundation_doctor(self) -> None:
        root = parser()
        for action in ("collect", "analyze", "candidates", "publish", "report"):
            parsed = root.parse_args(
                ["distill", action, "run-notes", "--request", "request.json"]
            )
            self.assertEqual(parsed.distillation_action, action)
        parsed = root.parse_args(
            ["distill", "decide", "run-notes", "--decision", "decision.json"]
        )
        self.assertEqual(parsed.distillation_action, "decide")
        self.assertEqual(root.parse_args(["doctor"]).command, "doctor")


if __name__ == "__main__":
    unittest.main()
