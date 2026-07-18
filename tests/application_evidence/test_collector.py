from __future__ import annotations

import unittest

from servicefabric_agentic_contracts import (
    AgentHandoff,
    AgentRunPlan,
    AgentTask,
    AgentTaskResult,
    ApplicationIntent,
    VerificationEvidence,
)
from servicefabric_application_evidence import (
    ApplicationEvidenceCollector,
    EvidenceCollectionError,
    EvidenceCollectionRequest,
    ManifestEvidence,
)


class ApplicationEvidenceCollectorTests(unittest.TestCase):
    def _request(self, *, changed_paths: tuple[str, ...] = ("src/notes.py",)) -> EvidenceCollectionRequest:
        plan = AgentRunPlan(
            run_id="notes-run",
            intent=ApplicationIntent(intent_id="notes-intent", mode="create", objective="Create notes", application_id="notes"),
            tasks=(AgentTask(task_id="notes-code", role="implementation", objective="Implement notes", allowed_paths=("src",)),),
            maximum_parallel_tasks=1,
        )
        handoff = AgentHandoff(
            run_id="notes-run", status="success",
            task_results=(AgentTaskResult(
                task_id="notes-code", status="success", changed_paths=changed_paths,
                evidence=(VerificationEvidence(command="python3 -m unittest", exit_code=0, summary="passed", artifact_ref="evidence:unit"),),
            ),),
        )
        return EvidenceCollectionRequest(
            bundle_id="notes-bundle", repository_head="abcdef0", application_blueprint_id="notes-blueprint",
            manifests=(ManifestEvidence(
                ref="manifest:notes", content='{"name":"notes"}', source_paths=("src",),
                operation_refs=("notes.search",), capability_refs=("capability:notes.search",),
                documentation_refs=("docs:notes",), verification_evidence_refs=("evidence:manifest",),
            ),), agent_run_plan=plan, agent_handoff=handoff, factory_run_id="notes-run",
        )

    def test_collects_deterministic_bundle_from_explicit_inputs(self) -> None:
        collector = ApplicationEvidenceCollector()
        first = collector.collect(self._request())
        second = collector.collect(self._request())
        self.assertEqual(first, second)
        self.assertEqual(first.changed_path_refs, ("src/notes.py",))
        self.assertEqual(first.verification_evidence_refs, ("evidence:manifest", "evidence:unit"))
        self.assertEqual(first.content_digests["manifest:notes"], "sha256:e687a7f62975eaa11c6608b418ac154160c34d681dc31a760752cc23e0680a34")

    def test_rejects_path_not_declared_by_manifest(self) -> None:
        with self.assertRaisesRegex(EvidenceCollectionError, "undeclared changed path"):
            ApplicationEvidenceCollector().collect(self._request(changed_paths=("other/notes.py",)))

    def test_rejects_result_without_planned_task(self) -> None:
        request = self._request()
        invalid = EvidenceCollectionRequest(
            **{**request.__dict__, "agent_handoff": AgentHandoff(
                run_id="notes-run", status="success",
                task_results=(AgentTaskResult(task_id="unknown", status="success"),),
            )}
        )
        with self.assertRaisesRegex(EvidenceCollectionError, "absent from plan"):
            ApplicationEvidenceCollector().collect(invalid)


if __name__ == "__main__":
    unittest.main()
