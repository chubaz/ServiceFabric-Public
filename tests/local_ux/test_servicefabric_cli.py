"""Subprocess acceptance tests for the local developer command."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
COMMAND = [os.environ.get("SERVICEFABRIC_COMMAND", "servicefabric")]


class LocalDeveloperUxTests(unittest.TestCase):
    def command(self, *args: str, home: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [*COMMAND, *args],
            cwd=ROOT,
            env={**os.environ, "SERVICEFABRIC_HOME": str(home)},
            capture_output=True,
            text=True,
        )

    def test_initialize_list_and_invoke_with_human_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary) / "workspace"
            first = self.command("init", home=home)
            second = self.command("init", home=home)
            tools = self.command("tools", "list", home=home)
            result = self.command(
                "invoke",
                "math.calculate",
                "--arguments",
                '{"expression":"1+2*3"}',
                home=home,
            )

            self.assertEqual(first.returncode, 0)
            self.assertIn("Created local workspace", first.stdout)
            self.assertEqual(second.returncode, 0)
            self.assertIn("Using local workspace", second.stdout)
            self.assertEqual(tools.returncode, 0)
            self.assertIn("math.calculate", tools.stdout)
            self.assertEqual(result.returncode, 0)
            self.assertIn("math.calculate -> 7", result.stdout)
            self.assertNotIn('"apiVersion"', result.stdout)

    def test_json_mode_works_after_the_subcommand(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary) / "workspace"
            self.assertEqual(self.command("init", home=home).returncode, 0)

            status = self.command("status", "--json", home=home)
            result = self.command(
                "invoke",
                "math.calculate",
                "--arguments",
                '{"expression":"40+2"}',
                "--json",
                home=home,
            )

            self.assertEqual(status.returncode, 0)
            self.assertEqual(json.loads(status.stdout)["tools"], 1)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(json.loads(result.stdout)["result"]["data"]["value"], 42)

    def test_safe_errors_and_help(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary) / "workspace"
            uninitialized = self.command("status", home=home)
            self.assertNotEqual(uninitialized.returncode, 0)
            self.assertIn("servicefabric init", uninitialized.stderr)

            self.assertEqual(self.command("init", home=home).returncode, 0)
            invalid = self.command(
                "invoke", "math.calculate", "--arguments", "{", home=home
            )
            unknown = self.command("tools", "describe", "not.real", home=home)
            help_output = self.command("--help", home=home)

            self.assertNotEqual(invalid.returncode, 0)
            self.assertNotIn("Traceback", invalid.stderr)
            self.assertNotEqual(unknown.returncode, 0)
            self.assertIn("not available locally", unknown.stderr)
            self.assertEqual(help_output.returncode, 0)
            self.assertIn("Start with: servicefabric init", help_output.stdout)
