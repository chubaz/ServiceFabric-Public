"""One black-box Wave-10 journey over a completed synthetic Wave-9 run."""

from __future__ import annotations

from contextlib import redirect_stdout
from hashlib import sha256
from io import StringIO
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from servicefabric_agent_provider_runtime import ProviderRuntime
from servicefabric_agentic_contracts import AgentRunPlan, AgentTaskResult
from servicefabric_agentic_run_store import FileRunStore
from servicefabric_application_factory_contracts import (
    ApplicationFactoryHandoff,
    EngineeringBlueprint,
    TechnologyProfile,
    UnmetRequirement,
)
from servicefabric_application_factory_state import FileFactoryLifecycleStore
from servicefabric_capability_model import CapabilityDefinition
from servicefabric_capability_registry import CapabilityRegistry
from servicefabric_distillation_contracts import (
    BlueprintEvolutionProposal,
    CapabilityCandidate,
    DistillationDecision,
    EngineeringPatternCandidate,
    SystemChangeProposal,
    TechniquePolicyCandidate,
    TechniquePolicyDefinition,
)
from servicefabric_engineering_distillation import EngineeringPatternCatalog
from servicefabric_operation_model import HttpBinding, OperationDefinition
from servicefabric_technique_policies import TechniquePolicyCatalog
from servicefabric_workspace import WorkspaceService, resolve_workspace

from servicefabric_client.application_factory import ApplicationFactoryService
from servicefabric_client.distillation import (
    DistillationInputs,
    DistillationService,
    FileDistillationDecisionStore,
    ManifestSource,
)
from servicefabric_client.main import as_json_value, main


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "wave_10" / "reviewed_distillation_journey.json"
SERVICEFABRIC_SOURCES = (
    ROOT / "clients" / "python" / "servicefabric_client" / "distillation.py",
    ROOT / "clients" / "python" / "servicefabric_client" / "application_factory.py",
    ROOT / "packages" / "servicefabric_application_evidence" / "src"
    / "servicefabric_application_evidence" / "collector.py",
    ROOT / "packages" / "servicefabric_capability_distillation" / "src"
    / "servicefabric_capability_distillation" / "distillation.py",
    ROOT / "packages" / "servicefabric_evolution_proposals" / "src"
    / "servicefabric_evolution_proposals" / "proposals.py",
)


def _canonical(value: object) -> str:
    return json.dumps(as_json_value(value), sort_keys=True, separators=(",", ":"))


def _snapshot(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _source_snapshot() -> dict[str, str]:
    return {
        path.relative_to(ROOT).as_posix(): sha256(path.read_bytes()).hexdigest()
        for path in SERVICEFABRIC_SOURCES
    }


class DistillationJourneyTests(unittest.TestCase):
    def test_completed_factory_run_distills_reviewed_knowledge_without_execution_or_mutation(self) -> None:
        scenario = json.loads(FIXTURE.read_text(encoding="utf-8"))
        run_id = scenario["run_id"]

        with tempfile.TemporaryDirectory(prefix="wave-10-evaluation-") as temporary:
            temporary_root = Path(temporary)
            application_root = temporary_root / "generated-application"
            for relative, content in scenario["generated_application"].items():
                target = application_root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")

            platform_home = temporary_root / "platform-state"
            factory_root = platform_home / "factory-runs" / "wave-09"
            plan = AgentRunPlan.model_validate(scenario["agent_run_plan"])
            profile = TechnologyProfile.model_validate(scenario["technology_profile"])
            engineering = EngineeringBlueprint.model_validate(
                {**scenario["engineering_blueprint"], "agent_run_plan": scenario["agent_run_plan"]}
            )
            unmet = UnmetRequirement.model_validate(scenario["unmet_requirement"])
            handoff = ApplicationFactoryHandoff.model_validate(
                {**scenario["factory_handoff"], "unmet_requirements": [scenario["unmet_requirement"]]}
            )

            plan_path = factory_root / "plans" / f"{run_id}.json"
            plan_path.parent.mkdir(parents=True, exist_ok=True)
            plan_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "run_id": run_id,
                        "application_id": scenario["application_id"],
                        "application_blueprint_id": scenario["application_blueprint_id"],
                        "application_blueprint_version": scenario["application_blueprint_version"],
                        "technology_profile": profile.model_dump(mode="json"),
                        "engineering_blueprint": engineering.model_dump(mode="json"),
                        "bootstrap": {"integration_worktree": str(application_root)},
                    },
                    sort_keys=True,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            run_store = FileRunStore(factory_root / "agent-runs" / "runs")
            run_store.save_plan(plan)
            for value in scenario["agent_task_results"]:
                run_store.record_result(run_id, AgentTaskResult.model_validate(value))
            lifecycle = FileFactoryLifecycleStore(factory_root / "lifecycle")
            lifecycle.record_unmet_requirement(unmet)
            lifecycle.record_handoff(handoff)

            request = scenario["distillation_request"]
            operations = tuple(
                OperationDefinition(
                    operation_id=value["operation_id"],
                    version=value["version"],
                    application_ref=value["application_ref"],
                    module_ref=value["module_ref"],
                    interface_ref=value["interface_ref"],
                    bindings=tuple(HttpBinding(**binding) for binding in value["bindings"]),
                )
                for value in request["operations"]
            )
            inputs = DistillationInputs(
                run_id=run_id,
                manifests=tuple(ManifestSource(**value) for value in request["manifests"]),
                declared_operations=operations,
                declared_capabilities=tuple(
                    CapabilityDefinition.model_validate(value) for value in request["capabilities"]
                ),
                technique_policy_definitions=tuple(
                    TechniquePolicyDefinition.model_validate(value)
                    for value in request["technique_policies"]
                ),
                blueprint_categories=request["blueprint_categories"],
                system_scopes=request["system_scopes"],
                engineering_pattern_version=request["engineering_pattern_version"],
            )

            catalog_root = temporary_root / "distillation-state"
            capability_registry = CapabilityRegistry(catalog_root / "capabilities")
            technique_catalog = TechniquePolicyCatalog(catalog_root / "technique-policies")
            engineering_catalog = EngineeringPatternCatalog(catalog_root / "engineering-patterns")
            service = DistillationService(
                ApplicationFactoryService(factory_root),
                capability_registry,
                technique_catalog,
                engineering_catalog,
                FileDistillationDecisionStore(catalog_root / "decisions"),
            )

            application_before = _snapshot(application_root)
            sources_before = _source_snapshot()
            manifest_reads: list[Path] = []
            original_read_bytes = Path.read_bytes

            def audited_read_bytes(path: Path) -> bytes:
                manifest_reads.append(path.resolve())
                return original_read_bytes(path)

            with mock.patch.object(
                ProviderRuntime,
                "execute",
                side_effect=AssertionError("Wave-10 distillation must not call a provider"),
            ) as provider_execute:
                with mock.patch.object(Path, "read_bytes", audited_read_bytes):
                    collected_first = service.collect(inputs).bundle
                    collected_second = service.collect(inputs).bundle

                declared_manifest = (application_root / "application.json").resolve()
                self.assertEqual(manifest_reads, [declared_manifest, declared_manifest])
                self.assertEqual(collected_first, collected_second)
                self.assertEqual(collected_first.exact_manifest_refs, ("manifest:notes",))
                self.assertEqual(
                    collected_first.changed_path_refs,
                    ("src/notes.py", "tests/test_notes.py"),
                )
                self.assertEqual(set(collected_first.content_digests), {"manifest:notes"})
                bounded_evidence = _canonical(collected_first)
                self.assertNotIn("undeclared", bounded_evidence.casefold())
                self.assertNotIn(scenario["undeclared_marker"], bounded_evidence)

                self.assertEqual(capability_registry.list(), ())
                analysis_first = service.analyze(inputs)
                analysis_second = service.analyze(inputs)
                self.assertEqual(_canonical(analysis_first), _canonical(analysis_second))
                self.assertTrue(all(result.status == "success" for result in analysis_first.collected.factory["agent_task_results"]))

                capability, = analysis_first.capability_candidates
                technique, = analysis_first.technique_policy_candidates
                pattern, = analysis_first.engineering_pattern_candidates
                blueprint, = analysis_first.blueprint_proposals
                system, = analysis_first.system_proposals
                self.assertIsInstance(capability, CapabilityCandidate)
                self.assertEqual(capability.operation_ref, "notes.search")
                self.assertIsInstance(technique, TechniquePolicyCandidate)
                self.assertEqual(technique.proposed_definition.policy_id, "python.web")
                self.assertIsInstance(pattern, EngineeringPatternCandidate)
                self.assertEqual(pattern.lane_topology, ("api", "integration", "assurance"))
                self.assertIsInstance(blueprint, BlueprintEvolutionProposal)
                self.assertEqual(blueprint.category, "verification")
                self.assertEqual(blueprint.status, "proposed")
                self.assertIsInstance(system, SystemChangeProposal)
                self.assertEqual(system.source_requirement_ref, unmet.requirement_id)
                self.assertEqual(system.status, "proposed")
                repeated_command = scenario["repeated_verification_command"]
                self.assertGreaterEqual(
                    sum(
                        repeated_command in task.verification_commands
                        for task in plan.tasks
                    ),
                    2,
                )

                approved = (capability, technique, pattern)
                for index, candidate in enumerate(approved, start=1):
                    service.decide(DistillationDecision(
                        decision_id=f"decision-approve-{index}",
                        candidate_ref=candidate.candidate_id,
                        decision="approve",
                        reason="The bounded evidence was reviewed.",
                        decided_by="wave-10-evaluator",
                    ))
                service.decide(DistillationDecision(
                    decision_id="decision-reject-blueprint",
                    candidate_ref=blueprint.proposal_id,
                    decision="reject",
                    reason="Retain the need as a proposal for later blueprint review.",
                    decided_by="wave-10-evaluator",
                ))

                first_report = service.report(inputs)
                state_after_first_publish = _snapshot(catalog_root)
                second_report = service.report(inputs)
                state_after_second_publish = _snapshot(catalog_root)
                self.assertEqual(_canonical(first_report), _canonical(second_report))
                self.assertEqual(state_after_first_publish, state_after_second_publish)
                self.assertEqual(
                    first_report.published_references,
                    (
                        "capability:notes.search",
                        "engineering-pattern:engineering-pattern.engineering-notes@1.0.0",
                        "technique-policy:python.web@1.0.0",
                    ),
                )
                self.assertEqual(len(capability_registry.list()), 1)
                self.assertEqual(len(technique_catalog.list()), 1)
                self.assertEqual(len(engineering_catalog.list()), 1)
                self.assertNotIn(blueprint.proposal_id, first_report.report.published_refs)
                self.assertNotIn(system.proposal_id, first_report.report.published_refs)
                self.assertNotIn(system.proposal_id, {item.candidate_ref for item in first_report.decisions})
                self.assertEqual(first_report.blueprint_proposals, (blueprint,))
                self.assertEqual(first_report.system_proposals, (system,))

                workspace_root = temporary_root / "workspace"
                workspace = resolve_workspace(explicit_workspace=workspace_root)
                WorkspaceService(workspace).initialize()
                output = StringIO()
                with mock.patch.dict(
                    os.environ,
                    {"SERVICEFABRIC_HOME": str(platform_home)},
                    clear=False,
                ), mock.patch(
                    "servicefabric_client.distillation.shutil.which",
                    return_value="/synthetic/provider",
                ), redirect_stdout(output):
                    doctor_code = main([
                        "--workspace", str(workspace_root), "doctor", "--json"
                    ])
                doctor = json.loads(output.getvalue())
                self.assertEqual(doctor_code, 0 if doctor["ok"] else 1)
                self.assertEqual(len(doctor["checks"]), 12)
                self.assertEqual(
                    {item["name"] for item in doctor["checks"]},
                    {
                        "package:servicefabric_application_evidence",
                        "package:servicefabric_capability_distillation",
                        "package:servicefabric_technique_policies",
                        "package:servicefabric_engineering_distillation",
                        "package:servicefabric_evolution_proposals",
                        "package:servicefabric_release_readiness",
                        "workspace",
                        "blueprint-and-kit-catalogs",
                        "provider-adapters",
                        "registries-and-catalogs",
                        "writable-state-paths",
                        "declared-executables",
                    },
                )
                self.assertTrue(
                    all(
                        set(item) <= {"name", "status", "detail", "count", "providers", "executables"}
                        for item in doctor["checks"]
                    )
                )
                self.assertLess(len(_canonical(doctor)), 10_000)
                self.assertNotIn(scenario["undeclared_marker"], _canonical(doctor))
                provider_execute.assert_not_called()

            self.assertEqual(_snapshot(application_root), application_before)
            self.assertEqual(_source_snapshot(), sources_before)


if __name__ == "__main__":
    unittest.main()
