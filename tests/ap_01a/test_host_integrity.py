"""Adversarial AP-01A host integrity and concurrency tests."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError

from servicefabric_application_host import LocalApplicationHost
from servicefabric_client.main import LocalRuntime


ROOT = Path(__file__).resolve().parents[2]
CLI = Path(sys.executable).parent / "servicefabric"
EXAMPLE = ROOT / "examples/text-utility"


class HostIntegrityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.home = Path(self.temporary.name) / "workspace"
        self.command("init", check=True)

    def tearDown(self) -> None:
        self.command("apps", "stop", "text-utility", check=False)
        self.temporary.cleanup()

    def command(self, *arguments: str, check: bool = False) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment["SERVICEFABRIC_HOME"] = str(self.home)
        result = subprocess.run(
            [str(CLI), *arguments],
            cwd=ROOT,
            env=environment,
            text=True,
            capture_output=True,
            timeout=30,
        )
        if check and result.returncode:
            self.fail(f"command failed ({result.returncode}): {result.stderr}")
        return result

    def popen(self, *arguments: str) -> subprocess.Popen[str]:
        environment = os.environ.copy()
        environment["SERVICEFABRIC_HOME"] = str(self.home)
        return subprocess.Popen(
            [str(CLI), *arguments],
            cwd=ROOT,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def install(self) -> None:
        self.command("apps", "install", str(EXAMPLE), check=True)

    def build(self) -> str:
        result = self.command("apps", "build", "text-utility", "--json", check=True)
        return str(json.loads(result.stdout)["build"]["artifact_digest"])

    def start(self) -> dict[str, object]:
        result = self.command("apps", "start", "text-utility", "--json", check=True)
        return json.loads(result.stdout)["start"]

    def test_concurrent_builds_publish_one_deterministic_artifact(self) -> None:
        self.install()
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = tuple(
                executor.map(
                    lambda _: self.command(
                        "apps", "build", "text-utility", "--json"
                    ),
                    range(2),
                )
            )
        self.assertEqual([item.returncode for item in results], [0, 0])
        digests = {
            json.loads(item.stdout)["build"]["artifact_digest"] for item in results
        }
        self.assertEqual(len(digests), 1)
        artifacts = json.loads(self.command("artifacts", "list", "--json").stdout)
        self.assertEqual(artifacts["artifacts"], list(digests))

    def test_concurrent_starts_own_one_process(self) -> None:
        self.install()
        self.build()
        first = self.popen("apps", "start", "text-utility", "--json")
        second = self.popen("apps", "start", "text-utility", "--json")
        first_output = first.communicate(timeout=30)
        second_output = second.communicate(timeout=30)
        self.assertEqual((first.returncode, second.returncode), (0, 0), first_output + second_output)
        status = json.loads(
            self.command("apps", "status", "text-utility", "--json", check=True).stdout
        )["status"]
        returned_pids = {
            json.loads(output[0])["start"]["pid"]
            for output in (first_output, second_output)
        }
        self.assertEqual(returned_pids, {status["pid"]})
        self.assertEqual(status["state"], "running")

    def test_stop_during_startup_leaves_no_orphan_process(self) -> None:
        self.install()
        self.build()
        process = self.popen("apps", "start", "text-utility", "--json")
        state_path = self.home / "hosted-applications/text-utility/application.json"
        launched_pid = None
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            record = json.loads(state_path.read_text(encoding="utf-8"))
            if record.get("state") == "starting":
                launched_pid = int(record["pid"])
                break
            time.sleep(0.005)
        self.assertIsNotNone(launched_pid)
        stopped = self.command("apps", "stop", "text-utility")
        process.communicate(timeout=30)
        status = json.loads(
            self.command("apps", "status", "text-utility", "--json", check=True).stdout
        )["status"]
        self.assertEqual(stopped.returncode, 0, stopped.stderr)
        self.assertEqual(status["state"], "stopped")
        with self.assertRaises(ProcessLookupError):
            os.kill(launched_pid, 0)

    def test_starting_state_is_observable_and_rejects_calls(self) -> None:
        self.install()
        self.build()
        process = self.popen("apps", "start", "text-utility", "--json")
        state_path = self.home / "hosted-applications/text-utility/application.json"
        observed = None
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            value = json.loads(state_path.read_text(encoding="utf-8"))
            if value.get("state") == "starting":
                observed = LocalApplicationHost(self.home).status("text-utility")
                with self.assertRaisesRegex(RuntimeError, "unavailable"):
                    LocalApplicationHost(self.home).invoke(
                        "text.count_words", {"text": "not yet"}
                    )
                break
            time.sleep(0.005)
        output = process.communicate(timeout=30)
        self.assertEqual(process.returncode, 0, output)
        self.assertIsNotNone(observed)
        self.assertEqual(observed["state"], "starting")

    def test_stale_pid_identity_never_signals_unrelated_process(self) -> None:
        self.install()
        self.build()
        path = self.home / "hosted-applications/text-utility/application.json"
        record = json.loads(path.read_text(encoding="utf-8"))
        record.update(
            {
                "state": "running",
                "pid": os.getpid(),
                "port": 1,
                "process_start_ticks": -1,
            }
        )
        path.write_text(json.dumps(record), encoding="utf-8")
        status = LocalApplicationHost(self.home).stop("text-utility")
        os.kill(os.getpid(), 0)
        self.assertEqual(status["state"], "failed")
        self.assertIsNone(status["pid"])

    def test_artifact_corruption_blocks_start(self) -> None:
        self.install()
        artifact = self.build()
        digest_value = artifact.removeprefix("sha256:")
        app_path = self.home / "artifacts/sha256" / digest_value[:2] / digest_value / "files/app.py"
        app_path.chmod(0o644)
        app_path.write_text("raise RuntimeError('corrupt')\n", encoding="utf-8")
        result = self.command("apps", "start", "text-utility")
        self.assertEqual(result.returncode, 1)
        self.assertIn("integrity verification", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_health_timeout_stops_real_process_and_records_failure(self) -> None:
        host = LocalApplicationHost(self.home, health_timeout_seconds=1.0)
        host.install(EXAMPLE)
        host.build("text-utility")
        with patch(
            "servicefabric_application_host.service.urlopen",
            side_effect=URLError("controlled unavailable probe"),
        ):
            with self.assertRaisesRegex(RuntimeError, "health check timed out"):
                host.start("text-utility")
        status = host.status("text-utility")
        self.assertEqual(status["state"], "failed")
        self.assertEqual(status["health"], "unavailable")

    def test_invalid_arguments_never_reach_application(self) -> None:
        self.install()
        self.build()
        self.start()
        before = json.loads(
            self.command("apps", "status", "text-utility", "--json", check=True).stdout
        )["status"]["request_count"]
        result = self.command(
            "call", "text.count_words", "--input", '{"text":"","extra":true}'
        )
        after = json.loads(
            self.command("apps", "status", "text-utility", "--json", check=True).stdout
        )["status"]["request_count"]
        self.assertEqual(result.returncode, 1)
        self.assertEqual((before, after), (0, 0))
        self.assertIn("input is invalid", result.stderr)

    def test_policy_denial_never_reaches_application(self) -> None:
        self.install()
        self.build()
        self.start()
        runtime = LocalRuntime(self.home)
        runtime.caller = runtime.caller.model_copy(update={"scopes": ("math-calculate",)})
        _request, result = runtime.invoke_application(
            "text.count_words", {"text": "must not execute"}
        )
        status = json.loads(
            self.command("apps", "status", "text-utility", "--json", check=True).stdout
        )["status"]
        self.assertEqual(result.status, "error")
        self.assertEqual(result.error.code, "SF-AUTHZ-DENIED")
        self.assertEqual(status["request_count"], 0)

    def test_modified_reviewed_action_is_rejected_at_install(self) -> None:
        package_root = Path(self.temporary.name) / "forged"
        package_root.mkdir()
        for name in ("app.py", "pyproject.toml", "servicefabric-package.json"):
            (package_root / name).write_bytes((EXAMPLE / name).read_bytes())
        manifest_path = package_root / "servicefabric-package.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["capabilities"][0]["path"] = "/arbitrary"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        result = self.command("apps", "install", str(package_root))
        self.assertEqual(result.returncode, 1)
        self.assertIn("not an approved", result.stderr)

    def test_malformed_state_and_stale_pending_write_are_safe(self) -> None:
        self.install()
        state = self.home / "hosted-applications/text-utility/application.json"
        pending = state.with_name("application.json.pending-interrupted")
        pending.write_text("{", encoding="utf-8")
        self.assertEqual(
            self.command("apps", "status", "text-utility").returncode, 0
        )
        state.write_text("{", encoding="utf-8")
        result = self.command("apps", "status", "text-utility")
        self.assertEqual(result.returncode, 1)
        self.assertIn("state is unreadable", result.stderr)
        self.assertNotIn(str(self.home), result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_unexpected_exit_reports_failed_and_unavailable_resources(self) -> None:
        self.install()
        self.build()
        started = self.start()
        os.kill(int(started["pid"]), signal.SIGKILL)
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            status = json.loads(
                self.command("apps", "status", "text-utility", "--json", check=True).stdout
            )["status"]
            if status["state"] == "failed":
                break
            time.sleep(0.02)
        resources = json.loads(
            self.command("apps", "resources", "text-utility", "--json", check=True).stdout
        )["resources"]
        self.assertEqual(status["state"], "failed")
        self.assertIsNone(resources["measured"]["current_memory_bytes"])
        self.assertIsNone(resources["measured"]["recent_cpu_percent"])
        call = self.command(
            "call", "text.count_words", "--input", '{"text":"must not run"}'
        )
        self.assertEqual(call.returncode, 1)
        self.assertIn("unavailable", call.stderr)

    def test_repeated_install_build_start_and_stop_are_bounded(self) -> None:
        self.install()
        self.assertIn(
            "Already installed",
            self.command("apps", "install", str(EXAMPLE), check=True).stdout,
        )
        first = self.build()
        second = self.build()
        self.assertEqual(first, second)
        first_start = self.start()
        second_start = self.start()
        self.assertEqual(first_start["pid"], second_start["pid"])
        self.assertEqual(self.command("apps", "stop", "text-utility").returncode, 0)
        self.assertEqual(self.command("apps", "stop", "text-utility").returncode, 0)


if __name__ == "__main__":
    unittest.main()
