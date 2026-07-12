from __future__ import annotations

import unittest

from pydantic import ValidationError

from servicefabric_contracts import ToolRevision
from test_service_package import load_fixture


class ToolRevisionTests(unittest.TestCase):
    def test_reference_revisions_validate(self) -> None:
        for name in ("tool_revision_math_calculate_v1.json", "tool_revision_research_search_papers_v1.json", "tool_revision_project_create_task_v1.json"):
            with self.subTest(name=name):
                revision = ToolRevision.model_validate(load_fixture(name))
                self.assertEqual(revision.spec.tool_id, revision.spec.definition_ref.tool_id)
                self.assertEqual(revision.spec.content_digest, revision.spec.calculated_content_digest())

    def test_revision_is_frozen(self) -> None:
        revision = ToolRevision.model_validate(load_fixture("tool_revision_math_calculate_v1.json"))
        with self.assertRaises(ValidationError):
            revision.spec.revision = "1.0.1"
        with self.assertRaises(ValidationError):
            revision.spec.execution_binding.function_ref = "other"

    def test_content_digest_calculation_is_deterministic(self) -> None:
        revision = ToolRevision.model_validate(load_fixture("tool_revision_math_calculate_v1.json"))
        self.assertEqual(revision.spec.calculated_content_digest(), revision.spec.calculated_content_digest())
        self.assertRegex(revision.spec.calculated_content_digest(), r"^sha256:[a-f0-9]{64}$")
        changed_payload = load_fixture("tool_revision_math_calculate_v1.json")
        changed_payload["spec"]["timeouts"]["maximum_timeout_ms"] = 1999
        changed = ToolRevision.model_validate(changed_payload)
        self.assertNotEqual(revision.spec.calculated_content_digest(), changed.spec.calculated_content_digest())

    def test_revision_aliases_and_missing_binding_are_rejected(self) -> None:
        payload = load_fixture("tool_revision_math_calculate_v1.json")
        payload["spec"]["revision"] = "latest"
        with self.assertRaises(ValidationError):
            ToolRevision.model_validate(payload)

    def test_revision_must_reference_its_definition(self) -> None:
        payload = load_fixture("tool_revision_math_calculate_v1.json")
        payload["spec"]["definition_ref"]["tool_id"] = "research.search_papers"
        with self.assertRaises(ValidationError):
            ToolRevision.model_validate(payload)
        payload = load_fixture("tool_revision_math_calculate_v1.json")
        del payload["spec"]["execution_binding"]
        with self.assertRaises(ValidationError):
            ToolRevision.model_validate(payload)
