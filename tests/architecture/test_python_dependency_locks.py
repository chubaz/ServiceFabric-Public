from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


class PythonDependencyLockTests(unittest.TestCase):
    def test_python_dependency_lock_guardrails_pass(self) -> None:
        result = subprocess.run(
            ["python3", "scripts/dependencies/check_python_locks.py"],
            cwd=REPOSITORY_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_nginx_uses_docker_runtime_dns_for_upstreams(self) -> None:
        content = (REPOSITORY_ROOT / "1_proxy" / "conf.d" / "default.conf").read_text(encoding="utf-8")
        self.assertIn("resolver 127.0.0.11", content)
        self.assertIn("set $django_upstream backend_api:8000;", content)
        self.assertIn("set $flask_upstream core_flask_service:5000;", content)
        self.assertIn("set $fastapi_upstream fastapi_core:8000;", content)
        self.assertIn("proxy_pass http://$django_upstream", content)
        self.assertIn("proxy_pass http://$flask_upstream", content)
        self.assertIn("proxy_pass http://$fastapi_upstream", content)
        self.assertNotRegex(content, r"(?m)^\s*upstream\s+")

    def test_django_entrypoint_passes_explicit_commands_through(self) -> None:
        content = (REPOSITORY_ROOT / "2_backend_api" / "entrypoint.sh").read_text(encoding="utf-8")
        self.assertIn('if [ "$#" -gt 0 ]; then', content)
        self.assertIn('exec "$@"', content)
        self.assertIn("exec gunicorn myproject.wsgi:application", content)
        self.assertNotIn("manage.py migrate", content)
        self.assertNotIn("collectstatic", content)
        self.assertNotIn("createsuperuser", content)
        self.assertNotIn("eval", content)


if __name__ == "__main__":
    unittest.main()
