from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
COMPOSE_FILES = [REPOSITORY_ROOT / "docker-compose.yml"]
APPLICATION_DOCKERFILES = {
    "proxy": REPOSITORY_ROOT / "1_proxy" / "Dockerfile",
    "backend_api": REPOSITORY_ROOT / "2_backend_api" / "Dockerfile",
    "core_flask_service": REPOSITORY_ROOT / "5_core_services" / "flask_base" / "Dockerfile",
    "fastapi_core": REPOSITORY_ROOT / "5_core_services" / "fastapi_base" / "Dockerfile",
}


def render_profile(profile: str) -> dict:
    example = REPOSITORY_ROOT / f".env.example.{profile}"
    with tempfile.NamedTemporaryFile("w", suffix=".env", delete=False) as handle:
        handle.write(example.read_text(encoding="utf-8"))
        environment_path = Path(handle.name)
    try:
        environment = os.environ | {"SERVICEFABRIC_ENV_FILE": str(environment_path)}
        result = subprocess.run(
            [
                "docker", "compose", "--env-file", str(environment_path),
                "-f", str(COMPOSE_FILES[0]), "-f", str(REPOSITORY_ROOT / f"docker-compose.{profile}.yml"),
                "config", "--format", "json",
            ],
            cwd=REPOSITORY_ROOT,
            capture_output=True,
            text=True,
            check=True,
            env=environment,
        )
        return json.loads(result.stdout)
    finally:
        environment_path.unlink(missing_ok=True)


class ComposeProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.production = render_profile("prod")
        cls.development = render_profile("dev")

    def test_production_contains_only_immutable_runtime_services(self) -> None:
        self.assertEqual(
            set(self.production["services"]),
            {"proxy", "backend_api", "db", "core_flask_service", "fastapi_core"},
        )

    def test_production_exposes_only_proxy(self) -> None:
        for name, service in self.production["services"].items():
            if name == "proxy":
                self.assertEqual(len(service.get("ports", [])), 1)
            else:
                self.assertFalse(service.get("ports"), name)

    def test_production_has_no_source_bind_mounts_or_development_commands(self) -> None:
        prohibited = ("runserver", "--reload", "npm install", "pip install")
        rendered = json.dumps(self.production)
        for token in prohibited:
            self.assertNotIn(token, rendered)
        for name, service in self.production["services"].items():
            for mount in service.get("volumes", []):
                self.assertNotEqual(mount.get("type"), "bind", f"{name}: {mount}")

    def test_production_has_health_checks_and_hardened_application_images(self) -> None:
        for name in ("proxy", "backend_api", "db", "core_flask_service", "fastapi_core"):
            self.assertIn("healthcheck", self.production["services"][name])
        for name, dockerfile in APPLICATION_DOCKERFILES.items():
            content = dockerfile.read_text(encoding="utf-8")
            self.assertRegex(content, r"(?m)^USER\s+(?!root\s*$).+$", msg=name)

    def test_development_retains_explicit_developer_facilities(self) -> None:
        services = self.development["services"]
        self.assertIn("fabric_watcher", services)
        self.assertIn("component_lab", services)
        self.assertIn("runserver", json.dumps(services["backend_api"]))
        self.assertTrue(services["backend_api"].get("ports"))
        self.assertTrue(services["component_lab"].get("ports"))

    def test_production_example_is_rejected_and_make_does_not_copy_it(self) -> None:
        command = ["python3", "scripts/compose/validate_production_env.py", ".env.example.prod"]
        result = subprocess.run(command, cwd=REPOSITORY_ROOT, capture_output=True, text=True, check=False)
        self.assertNotEqual(result.returncode, 0)
        makefile = (REPOSITORY_ROOT / "Makefile").read_text(encoding="utf-8")
        prod_target = makefile.split("prod:", 1)[1].split("prod-preflight:", 1)[0]
        self.assertNotIn("cp .env.example.prod", prod_target)


if __name__ == "__main__":
    unittest.main()
