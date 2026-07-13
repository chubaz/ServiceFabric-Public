"""Hosting-only acceptance tests for the stable AP-01A local hosting baseline."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CLI = Path(sys.executable).parent / "servicefabric"


class HostingBaselineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.home = Path(self.temporary.name) / "workspace"

    def tearDown(self) -> None:
        # Best effort cleanup
        try:
            self.command("apps", "stop", "text-utility", check=False)
        except Exception:
            pass
        self.temporary.cleanup()

    def command(self, *arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
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
        
        # Rigorous check for tracebacks in CLI output (both stdout and stderr)
        combined_output = result.stdout + result.stderr
        self.assertNotIn("Traceback", combined_output, f"Traceback detected in command output:\n{combined_output}")
        
        return result

    def test_hosting_baseline_journey(self) -> None:
        # 1. Initialize workspace
        init_res = self.command("init")
        self.assertIn("Created local workspace", init_res.stdout)

        # 2. Install application (succeeds and is idempotent)
        install_path = str(ROOT / "examples/text-utility")
        install1 = self.command("apps", "install", install_path)
        self.assertIn("Installed", install1.stdout)

        install2 = self.command("apps", "install", install_path)
        self.assertIn("Already installed", install2.stdout)

        # 3. Repeated builds produce the same artifact (deterministic build)
        build1 = self.command("apps", "build", "text-utility", "--json")
        digest1 = json.loads(build1.stdout)["build"]["artifact_digest"]
        self.assertTrue(bool(digest1))

        build2 = self.command("apps", "build", "text-utility", "--json")
        digest2 = json.loads(build2.stdout)["build"]["artifact_digest"]
        self.assertEqual(digest1, digest2, "Repeated builds must produce the same artifact digest")

        # 4. Startup produces one owned process and becomes healthy
        start_res = self.command("apps", "start", "text-utility", "--json")
        start_data = json.loads(start_res.stdout)["start"]
        pid = start_data["pid"]
        self.assertIsInstance(pid, int)

        # Assert startup produces one owned process
        # Check if process is alive (os.kill with 0 does not terminate, only checks existence)
        try:
            os.kill(pid, 0)
        except OSError:
            self.fail(f"Started process with PID {pid} is not running")

        # 5. Status identifies the running application and health becomes healthy
        status_res = self.command("apps", "status", "text-utility", "--json")
        status_data = json.loads(status_res.stdout)["status"]
        self.assertEqual(status_data["state"], "running")
        self.assertEqual(status_data["pid"], pid)
        self.assertEqual(status_data["health"], "healthy")

        # 6. Resource output separates declarations from measurements
        resources_res = self.command("apps", "resources", "text-utility", "--json")
        resources_data = json.loads(resources_res.stdout)["resources"]
        
        # Verify separate declarations from measurements
        self.assertIn("declared", resources_data)
        self.assertIn("measured", resources_data)
        
        self.assertEqual(resources_data["declared"]["memory_mib"], 128)
        self.assertGreater(resources_data["measured"]["current_memory_bytes"], 0)
        self.assertIsNotNone(resources_data["measured"]["recent_cpu_percent"])

        # 7. Stop terminates the owned process
        stop1 = self.command("apps", "stop", "text-utility")
        self.assertIn("text-utility: stopped", stop1.stdout)

        # Wait up to 5 seconds for the process to be completely terminated and cleaned up
        terminated = False
        for _ in range(50):
            try:
                os.kill(pid, 0)
                time.sleep(0.1)
            except OSError:
                terminated = True
                break
        self.assertTrue(terminated, f"Process with PID {pid} was not terminated after stop")

        # Assert status identifies the application as stopped
        status_stopped = self.command("apps", "status", "text-utility", "--json")
        status_stopped_data = json.loads(status_stopped.stdout)["status"]
        self.assertEqual(status_stopped_data["state"], "stopped")

        # 8. Repeated stop succeeds safely
        stop2 = self.command("apps", "stop", "text-utility")
        self.assertIn("text-utility: stopped", stop2.stdout)


if __name__ == "__main__":
    unittest.main()
