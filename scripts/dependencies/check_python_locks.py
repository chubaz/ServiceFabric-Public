#!/usr/bin/env python3
"""Validate service-local Python dependency inputs, locks, and Dockerfile usage."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class ServiceDependencies:
    name: str
    runtime_input: Path
    runtime_lock: Path
    dockerfile: Path | None
    production: bool = True


SERVICES = (
    ServiceDependencies(
        name="backend_api",
        runtime_input=REPOSITORY_ROOT / "2_backend_api" / "requirements" / "runtime.in",
        runtime_lock=REPOSITORY_ROOT / "2_backend_api" / "requirements" / "runtime.lock",
        dockerfile=REPOSITORY_ROOT / "2_backend_api" / "Dockerfile",
    ),
    ServiceDependencies(
        name="core_flask_service",
        runtime_input=REPOSITORY_ROOT / "5_core_services" / "flask_base" / "requirements" / "runtime.in",
        runtime_lock=REPOSITORY_ROOT / "5_core_services" / "flask_base" / "requirements" / "runtime.lock",
        dockerfile=REPOSITORY_ROOT / "5_core_services" / "flask_base" / "Dockerfile",
    ),
    ServiceDependencies(
        name="fastapi_core",
        runtime_input=REPOSITORY_ROOT / "5_core_services" / "fastapi_base" / "requirements" / "runtime.in",
        runtime_lock=REPOSITORY_ROOT / "5_core_services" / "fastapi_base" / "requirements" / "runtime.lock",
        dockerfile=REPOSITORY_ROOT / "5_core_services" / "fastapi_base" / "Dockerfile",
    ),
    ServiceDependencies(
        name="fabric_watcher",
        runtime_input=REPOSITORY_ROOT / "5_core_services" / "fabric_watcher" / "requirements" / "runtime.in",
        runtime_lock=REPOSITORY_ROOT / "5_core_services" / "fabric_watcher" / "requirements" / "runtime.lock",
        dockerfile=REPOSITORY_ROOT / "5_core_services" / "fabric_watcher" / "Dockerfile",
        production=False,
    ),
)

# Contract tests are not production image dependencies, but their lock is still
# source-controlled and must be reproducible.
CONTRACT_TEST_LOCK = ServiceDependencies(
    name="servicefabric_contracts_tests",
    runtime_input=REPOSITORY_ROOT / "packages" / "servicefabric_contracts" / "requirements" / "test.in",
    runtime_lock=REPOSITORY_ROOT / "packages" / "servicefabric_contracts" / "requirements" / "test.lock",
    dockerfile=None,
    production=False,
)


DISPLACED_FLASK_CAPABILITIES = {
    "beautifulsoup4",
    "chromadb",
    "crewai",
    "google-genai",
    "googlesearch-python",
    "langchain-community",
    "langchain-openai",
    "markdown",
    "numpy",
    "pandas",
    "polars",
    "pypdf2",
    "quantstats",
    "requests",
    "scikit-learn",
    "scipy",
    "statsmodels",
    "yfinance",
}


DIRECT_PIN_RE = re.compile(
    r"^(?P<name>[A-Za-z0-9_.-]+)(?:\[[A-Za-z0-9_,.-]+\])?==(?P<version>[^#;\s]+)(?:\s*;.*)?$"
)


def normalize_name(name: str) -> str:
    return name.replace("_", "-").lower()


def read_requirements(path: Path) -> list[tuple[int, str]]:
    requirements: list[tuple[int, str]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.split("#", 1)[0].strip()
        if not stripped:
            continue
        requirements.append((line_number, stripped))
    return requirements


def parse_direct_pin(requirement: str) -> tuple[str, str] | None:
    match = DIRECT_PIN_RE.match(requirement)
    if not match:
        return None
    return normalize_name(match.group("name")), match.group("version")


def strip_pip_compile_header(content: str) -> str:
    lines = content.splitlines()
    index = 0
    while index < len(lines) and (not lines[index].strip() or lines[index].startswith("#")):
        index += 1
    return "\n".join(lines[index:]).strip() + "\n"


def validate_runtime_input(service: ServiceDependencies) -> list[str]:
    errors: list[str] = []
    seen: dict[str, tuple[int, str]] = {}
    for line_number, requirement in read_requirements(service.runtime_input):
        parsed = parse_direct_pin(requirement)
        if parsed is None:
            errors.append(
                f"{service.name}: {service.runtime_input.relative_to(REPOSITORY_ROOT)}:{line_number} "
                "must be an exact direct runtime pin"
            )
            continue
        name, version = parsed
        if name in seen:
            previous_line, previous_version = seen[name]
            errors.append(
                f"{service.name}: duplicate direct requirement {name} at lines "
                f"{previous_line} and {line_number} ({previous_version}, {version})"
            )
            continue
        seen[name] = (line_number, version)
    return errors


def validate_runtime_lock(service: ServiceDependencies) -> list[str]:
    errors: list[str] = []
    if not service.runtime_lock.exists():
        return [f"{service.name}: missing lock file {service.runtime_lock.relative_to(REPOSITORY_ROOT)}"]

    locked_names: set[str] = set()
    for line_number, requirement in read_requirements(service.runtime_lock):
        parsed = parse_direct_pin(requirement)
        if parsed is None:
            errors.append(
                f"{service.name}: {service.runtime_lock.relative_to(REPOSITORY_ROOT)}:{line_number} "
                "must contain exact resolved pins only"
            )
            continue
        locked_names.add(parsed[0])

    for _, requirement in read_requirements(service.runtime_input):
        parsed = parse_direct_pin(requirement)
        if parsed and parsed[0] not in locked_names:
            errors.append(f"{service.name}: direct dependency {parsed[0]} is missing from runtime lock")

    if service.name == "core_flask_service":
        displaced = sorted(locked_names & DISPLACED_FLASK_CAPABILITIES)
        if displaced:
            errors.append(
                "core_flask_service: optional/domain packages must not be in the production lock: "
                + ", ".join(displaced)
            )
    return errors


def validate_dockerfile(service: ServiceDependencies) -> list[str]:
    if service.dockerfile is None:
        return []
    content = service.dockerfile.read_text(encoding="utf-8")
    errors: list[str] = []
    if "requirements/runtime.lock" not in content:
        errors.append(f"{service.name}: Dockerfile must install from requirements/runtime.lock")
    if re.search(r"pip\s+install[^\n]+-r\s+requirements\.txt", content):
        errors.append(f"{service.name}: Dockerfile must not install production dependencies from requirements.txt")
    return errors


def validate_lock_freshness(service: ServiceDependencies, pip_compile: str) -> list[str]:
    with tempfile.NamedTemporaryFile("w+", suffix=".lock", delete=False) as handle:
        temporary_lock = Path(handle.name)
    try:
        environment = os.environ | {
            "PIP_TOOLS_CACHE_DIR": os.environ.get(
                "PIP_TOOLS_CACHE_DIR", "/tmp/servicefabric-pip-tools-cache"
            ),
            "PIP_CACHE_DIR": os.environ.get("PIP_CACHE_DIR", "/tmp/servicefabric-pip-cache"),
        }
        command = [
            pip_compile,
            "--resolver=backtracking",
            "--no-emit-index-url",
            "--no-emit-trusted-host",
            "--allow-unsafe",
            f"--output-file={temporary_lock}",
            str(service.runtime_input.relative_to(REPOSITORY_ROOT)),
        ]
        result = subprocess.run(
            command,
            cwd=REPOSITORY_ROOT,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return [f"{service.name}: pip-compile failed:\n{result.stderr.strip()}"]

        expected = strip_pip_compile_header(service.runtime_lock.read_text(encoding="utf-8"))
        actual = strip_pip_compile_header(temporary_lock.read_text(encoding="utf-8"))
        if expected != actual:
            return [f"{service.name}: runtime.lock is stale relative to runtime.in"]
        return []
    finally:
        temporary_lock.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--verify-compile",
        action="store_true",
        help="Regenerate locks with pip-compile and fail if committed lock contents differ.",
    )
    args = parser.parse_args()

    errors: list[str] = []
    all_locks = SERVICES + (CONTRACT_TEST_LOCK,)
    for service in all_locks:
        errors.extend(validate_runtime_input(service))
        errors.extend(validate_runtime_lock(service))
        errors.extend(validate_dockerfile(service))

    if args.verify_compile:
        pip_compile = shutil.which("pip-compile")
        if not pip_compile:
            errors.append("pip-compile is required for --verify-compile")
        else:
            for service in all_locks:
                errors.extend(validate_lock_freshness(service, pip_compile))

    if errors:
        print("Python dependency lock validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("Python dependency locks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
