from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "packages" / "servicefabric_release_readiness"
sys.path.insert(0, str(PACKAGE_ROOT))

from servicefabric_release_readiness.doctor import run_doctor


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


class DoctorTests(unittest.TestCase):
    def test_current_repository_passes_declared_checks(self) -> None:
        report = run_doctor(REPOSITORY_ROOT)

        self.assertTrue(report.ok)
        self.assertEqual(report.release, "foundation-0.1")
        self.assertTrue(all(check.status == "pass" for check in report.checks))

    def test_missing_package_is_reported_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            report = run_doctor(temporary_directory)

        self.assertFalse(report.ok)
        self.assertEqual(report.checks[1].status, "fail")
        self.assertIn("missing packages/servicefabric_contracts/pyproject.toml", report.checks[1].detail)

    def test_cli_json_is_deterministic_and_machine_readable(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "servicefabric_release_readiness.cli",
                "doctor",
                "--repository-root",
                str(REPOSITORY_ROOT),
                "--json",
            ],
            check=False,
            capture_output=True,
            cwd=REPOSITORY_ROOT,
            env={**__import__("os").environ, "PYTHONPATH": str(PACKAGE_ROOT)},
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["release"], "foundation-0.1")


if __name__ == "__main__":
    unittest.main()
