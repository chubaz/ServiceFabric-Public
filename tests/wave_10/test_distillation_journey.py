"""Pending black-box composition journey for the Wave-10 distillation release."""

from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "wave_10" / "reviewed_distillation_journey.json"


@unittest.skip(
    "Pending Wave-10 integration composition: the authoritative distillation service, "
    "CLI, and publication adapters are not composed on this specialist branch."
)
class DistillationJourneyTests(unittest.TestCase):
    def test_reviewed_evidence_publishes_only_approved_candidates_deterministically(self) -> None:
        """Exercise the final public journey without bypassing authoritative catalogs.

        Integration must activate this test using its composed public CLI/service.  The
        journey supplies only the declared Wave-9 application evidence, verifies that
        the evidence bundle is manifest-bounded, reviews every candidate explicitly,
        and runs publication twice.  Only approved capability, technique-policy, and
        engineering-pattern candidates may reach their authoritative catalogs.  The
        rejected blueprint and system proposals remain non-executable records.
        """
        scenario = json.loads(FIXTURE.read_text(encoding="utf-8"))

        # The integration-owned composition supplies the public invocation here.  Do
        # not replace it with direct package calls: that would bypass the CLI/service
        # boundary that this black-box journey is intended to protect.
        self.assertEqual("sample-factory", scenario["application_id"])
        self.assertEqual(
            ["capability", "technique_policy", "engineering_pattern"],
            scenario["expected"]["published_candidate_kinds"],
        )
        self.assertTrue(scenario["expected"]["idempotent_publication"])
        self.assertTrue(scenario["expected"]["deterministic_report"])


if __name__ == "__main__":
    unittest.main()
