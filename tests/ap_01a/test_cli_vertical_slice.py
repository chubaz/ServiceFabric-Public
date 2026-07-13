"""Installed-CLI acceptance tests for the real AP-01A FastAPI process."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CLI = Path(sys.executable).parent / "servicefabric"


class HostedVerticalSliceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.home = Path(cls.temporary.name) / "workspace"
        cls.command("init")
        cls.command("apps", "install", str(ROOT / "examples/text-utility"))
        cls.command("apps", "build", "text-utility")
        cls.command("apps", "start", "text-utility")

    @classmethod
    def tearDownClass(cls):
        cls.command("apps", "stop", "text-utility", check=False)
        cls.temporary.cleanup()

    @classmethod
    def command(cls, *arguments: str, check: bool = True):
        environment = os.environ.copy()
        environment["SERVICEFABRIC_HOME"] = str(cls.home)
        result = subprocess.run([str(CLI), *arguments], cwd=ROOT, env=environment, text=True, capture_output=True)
        if check and result.returncode:
            raise AssertionError(f"command failed ({result.returncode}): {result.stderr}")
        return result

    def test_01_help_and_repeated_install(self):
        self.assertIn("local developer command", self.command("--help").stdout)
        self.assertIn("Already installed", self.command("apps", "install", str(ROOT / "examples/text-utility")).stdout)

    def test_02_status_and_real_health(self):
        output = self.command("apps", "status", "text-utility", "--json")
        self.assertEqual(json.loads(output.stdout)["status"]["health"], "healthy")

    def test_03_resource_observation_separates_declared_and_measured(self):
        value = json.loads(self.command("apps", "resources", "text-utility", "--json").stdout)["resources"]
        self.assertEqual(value["declared"]["memory_mib"], 128)
        self.assertGreater(value["measured"]["current_memory_bytes"], 0)

    def test_04_discovery_and_description(self):
        self.assertIn("text.count_words", self.command("tools", "list").stdout)
        self.assertIn("Text Utility", self.command("tools", "describe", "text.count_words").stdout)

    def test_05_real_governed_capability_invocation(self):
        value = json.loads(self.command("call", "text.count_words", "--input", '{"text":"ServiceFabric hosts applications and capabilities."}', "--json").stdout)
        self.assertEqual(value["policy_outcome"], "allow")
        self.assertEqual(value["result"]["data"]["word_count"], 5)

    def test_06_invalid_input_unknown_tool_and_safe_errors(self):
        invalid = self.command("call", "text.count_words", "--input", "not-json", check=False)
        self.assertEqual(invalid.returncode, 1)
        self.assertNotIn("Traceback", invalid.stderr)
        unknown = self.command("call", "unknown.tool", "--input", "{}", check=False)
        self.assertEqual(unknown.returncode, 1)

    def test_07_unexpected_exit_is_detected(self):
        state = json.loads(self.command("apps", "status", "text-utility", "--json").stdout)["status"]
        os.kill(state["pid"], signal.SIGTERM)
        for _ in range(50):
            value = json.loads(self.command("apps", "status", "text-utility", "--json").stdout)["status"]
            if value["state"] == "failed":
                break
        self.assertEqual(value["state"], "failed")
        self.command("apps", "start", "text-utility")

    def test_08_stop_makes_capability_unavailable(self):
        self.command("apps", "stop", "text-utility")
        result = self.command("call", "text.count_words", "--input", '{"text":"must not execute"}', check=False)
        self.assertEqual(result.returncode, 1)
        self.assertIn("unavailable", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


class ArchitectureTests(unittest.TestCase):
    def test_cli_does_not_import_example_or_fastapi_implementation(self):
        source = (ROOT / "clients/python/servicefabric_client/main.py").read_text(encoding="utf-8")
        self.assertNotIn("examples.text", source)
        self.assertNotIn("from fastapi", source)
        self.assertNotIn("/actions/count-words", source)

    def test_host_has_no_shell_execution_or_public_binding(self):
        source = (ROOT / "services/application_host/servicefabric_application_host/service.py").read_text(encoding="utf-8")
        self.assertNotIn("shell=True", source)
        self.assertNotIn("0.0.0.0", source)
        self.assertNotIn("os.system", source)


class FailureJourneyTests(unittest.TestCase):
    def command(self, home: Path, *arguments: str):
        environment = os.environ.copy()
        environment["SERVICEFABRIC_HOME"] = str(home)
        return subprocess.run([str(CLI), *arguments], cwd=ROOT, env=environment, text=True, capture_output=True)

    def test_application_not_installed_and_build_failure_are_safe(self):
        with tempfile.TemporaryDirectory() as directory:
            home=Path(directory)/"workspace"
            self.assertEqual(self.command(home,"init").returncode,0)
            start=self.command(home,"apps","start","text-utility")
            build=self.command(home,"apps","build","text-utility")
            self.assertEqual((start.returncode,build.returncode),(1,1))
            self.assertNotIn("Traceback",start.stderr+build.stderr)

    def test_start_failure_is_recorded_without_traceback(self):
        with tempfile.TemporaryDirectory() as directory:
            home=Path(directory)/"workspace"
            self.command(home,"init")
            self.command(home,"apps","install",str(ROOT/"examples/text-utility"))
            (home/"hosted-applications/text-utility/source/app.py").write_text("raise RuntimeError('fixture failure')\n",encoding="utf-8")
            self.command(home,"apps","build","text-utility")
            result=self.command(home,"apps","start","text-utility")
            self.assertEqual(result.returncode,1)
            self.assertNotIn("Traceback",result.stderr)
            status=json.loads(self.command(home,"apps","status","text-utility","--json").stdout)["status"]
            self.assertEqual(status["state"],"failed")

    def test_invalid_capability_input_is_safe(self):
        with tempfile.TemporaryDirectory() as directory:
            home=Path(directory)/"workspace"
            self.command(home,"init");self.command(home,"apps","install",str(ROOT/"examples/text-utility"));self.command(home,"apps","build","text-utility");self.command(home,"apps","start","text-utility")
            try:
                result=self.command(home,"call","text.count_words","--input",'{"text":""}')
                self.assertEqual(result.returncode,1)
                self.assertIn("input is invalid",result.stderr)
                self.assertNotIn("Traceback",result.stderr)
            finally:
                self.command(home,"apps","stop","text-utility")


if __name__ == "__main__":
    unittest.main()
