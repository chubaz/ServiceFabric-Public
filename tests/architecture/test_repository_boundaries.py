from __future__ import annotations

import hashlib
import json
import subprocess
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SPECIFICATION_MAP = REPOSITORY_ROOT / "docs" / "architecture" / "specification-map.md"
ADR_DIR = REPOSITORY_ROOT / "docs" / "architecture" / "adr"
DEBT_REGISTER = REPOSITORY_ROOT / "docs" / "refactoring" / "debt-register.yaml"
ARCHITECTURE_CHECK = REPOSITORY_ROOT / "scripts" / "architecture" / "check_legacy_patterns.py"

CANONICAL_DOCUMENTS = {
    "Canonical ServiceFabric Tool Manifest v1.md": "4af5d93b43aee8e519eccff09de03d0e15a9eb1e246987c79e6b95f3800efe67",
    "ServiceFabric Tool Capsule Runtime Framework v1.md": "7f502b99cfbc1f82d26a2309afc69f15bcf5e9aec44fadf0b6db3d2906769115",
    "Building Graph Specification v1.md": "6a75d960b9853a97dbb53d29cf1dc916c669ff63b3f4985525438487d899cb9b",
    "ServiceFabric System-Maintenance Graph Specifica.md": "08add4629777bc36edaab0edb904f60d5d4062e510dfbba4b75f6d4ff0fc466a",
    "ServiceFabric System-Evolution Graph Specificati.md": "5091741812b0a0d9361e9b052b53f4654403743cd930588fdf4c1b2d7ffe7243",
    "ServiceFabric Tool Registry  Capability Discover.md": "711b798b3788b32e2daedac492dd55d5045742d002c6e6adea98edacee637526",
    "ServiceFabric Security  Identity  Authorization.md": "7aedbf3de6e521666b4552b78489c82b9facbac92b03d288495f9caba8f12819",
    "ServiceFabric Telemetry  Evaluation  and Agent-C.md": "57b5dcebc8ac22d53522cda8c9a79e97124f5a19deccc4f62778b083a20b1e4e",
    "ServiceFabric Domain Tool Portfolio and Prioriti.md": "fa16195442fb5502bfebff6c0bc4f9ef9caba6a492d2b5534b48fd9b601f708c",
    "servicefabric-stage11/README.md": "f74342810483a96c9d54208cb2f889df37ddfd8a3ffc6dd86727f6de11f97b42",
    "ServiceFabric Production Architecture  Roadmap.md": "1a879d5fafad028734d046467e8ed3c496e890f44904d7223824b821ab3e1208",
}

REQUIRED_DEBT_IDS = {
    "LEGACY-DYNAMIC-IMPORT",
    "LEGACY-FLASK-CREATE-ALL",
    "INSECURE-INTERNAL-TOKEN",
    "UNAUTHENTICATED-VECTOR-ENDPOINTS",
    "UNAUTHENTICATED-RELOAD",
    "FALSE-PRODUCTION-PROFILE",
    "FASTAPI-RELOAD-IN-CONTAINER",
    "PLAINTEXT-PROVIDER-TOKENS",
}


class RepositoryBoundaryTests(unittest.TestCase):
    def test_specification_map_includes_every_canonical_document(self) -> None:
        content = SPECIFICATION_MAP.read_text(encoding="utf-8")
        for relative_path, expected_hash in CANONICAL_DOCUMENTS.items():
            self.assertIn(relative_path, content)
            self.assertIn(expected_hash, content)
            target = ((REPOSITORY_ROOT.parent / relative_path) if relative_path.startswith("servicefabric-stage11/") else (REPOSITORY_ROOT / "docs/canonical" / relative_path))
            actual_hash = hashlib.sha256(target.read_bytes()).hexdigest()
            self.assertEqual(actual_hash, expected_hash)

    def test_every_adr_has_status_and_date(self) -> None:
        adr_files = sorted(ADR_DIR.glob("*.md"))
        self.assertGreaterEqual(len(adr_files), 5)
        for path in adr_files:
            content = path.read_text(encoding="utf-8")
            self.assertTrue(
                "Status: Accepted" in content
                or "## Status\nAccepted" in content,
                msg=path.name,
            )
            if "Status: Accepted" in content:
                self.assertRegex(content, r"Date: \d{4}-\d{2}-\d{2}", msg=path.name)

    def test_every_known_unsafe_pattern_is_recorded(self) -> None:
        with DEBT_REGISTER.open("r", encoding="utf-8") as handle:
            debt_items = json.load(handle)
        identifiers = {item["id"] for item in debt_items}
        self.assertTrue(REQUIRED_DEBT_IDS.issubset(identifiers))

    def test_no_unrecorded_occurrence_of_prohibited_legacy_pattern_exists(self) -> None:
        result = subprocess.run(
            ["python3", str(ARCHITECTURE_CHECK)],
            cwd=REPOSITORY_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
