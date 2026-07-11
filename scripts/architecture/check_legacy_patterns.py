#!/usr/bin/env python3
"""Reject new occurrences of prohibited legacy patterns outside the debt allowlist."""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEBT_REGISTER_PATH = REPOSITORY_ROOT / "docs" / "refactoring" / "debt-register.yaml"

EXCLUDED_PARTS = {
    ".git",
    ".github",
    "__pycache__",
    "docs",
    "tests/architecture",
    "scripts/architecture",
    ".claude",
}

TEXT_EXTENSIONS = {
    ".py",
    ".sh",
    ".yml",
    ".yaml",
    ".json",
    ".ini",
    ".cfg",
    ".conf",
    ".toml",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".md",
}


@dataclass(frozen=True)
class Rule:
    identifier: str
    pattern: str
    description: str
    matcher: str = "literal"
    file_filter: tuple[str, ...] = ()


RULES = (
    Rule(
        identifier="LEGACY-DYNAMIC-IMPORT",
        pattern="run_script_for_instance(",
        description="dynamic script execution entrypoints",
    ),
    Rule(
        identifier="LEGACY-FLASK-CREATE-ALL",
        pattern="db.create_all(",
        description="implicit schema creation",
    ),
    Rule(
        identifier="FASTAPI-RELOAD-IN-CONTAINER",
        pattern=r"uvicorn.*--reload",
        description="reload-enabled uvicorn container commands",
        matcher="regex",
    ),
    Rule(
        identifier="FALSE-PRODUCTION-PROFILE",
        pattern="manage.py runserver",
        description="Django dev server in production-oriented files",
        file_filter=("prod",),
    ),
    Rule(
        identifier="INSECURE-INTERNAL-TOKEN",
        pattern="super-secret-fabric-key",
        description="hard-coded internal shared secret",
    ),
    Rule(
        identifier="UNAUTHENTICATED-RELOAD",
        pattern=r"route\(\s*['\"]/(_internal|[^'\"]*_internal[^'\"]*)",
        description="internal route declarations",
        matcher="regex",
    ),
    Rule(
        identifier="DOCKER-SOCKET-MOUNT",
        pattern="docker.sock",
        description="Docker socket mounts",
    ),
    Rule(
        identifier="PLAINTEXT-PROVIDER-TOKENS",
        pattern=r"\b[a-zA-Z_]*token[a-zA-Z_]*\s*=\s*models\.(CharField|TextField)\(",
        description="plaintext token model fields",
        matcher="regex",
    ),
)


def load_debt_register() -> dict[str, set[str]]:
    with DEBT_REGISTER_PATH.open("r", encoding="utf-8") as handle:
        items = json.load(handle)
    return {
        item["id"]: {str(Path(path).as_posix()) for path in item.get("paths", [])}
        for item in items
    }


def is_excluded(path: Path) -> bool:
    relative = path.relative_to(REPOSITORY_ROOT).as_posix()
    for part in EXCLUDED_PARTS:
        if relative == part or relative.startswith(part + "/"):
            return True
    return False


def should_scan(path: Path) -> bool:
    if not path.is_file() or is_excluded(path):
        return False
    return path.suffix in TEXT_EXTENSIONS or path.name in {"Dockerfile", "Makefile"}


def find_matches(path: Path, rule: Rule) -> bool:
    relative = path.relative_to(REPOSITORY_ROOT).as_posix()
    if rule.file_filter and not any(token in relative for token in rule.file_filter):
        return False

    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return False

    filtered_lines = []
    for line in content.splitlines():
        stripped = line.lstrip()
        if stripped.startswith(("#", "//", "*", "<!--")):
            continue
        filtered_lines.append(line)
    content = "\n".join(filtered_lines)

    if rule.matcher == "regex":
        return re.search(rule.pattern, content, flags=re.MULTILINE) is not None
    return rule.pattern in content


def main() -> int:
    debt_paths = load_debt_register()
    violations: list[str] = []

    for rule in RULES:
        allowed = debt_paths.get(rule.identifier, set())
        for path in REPOSITORY_ROOT.rglob("*"):
            if not should_scan(path):
                continue
            if not find_matches(path, rule):
                continue
            relative = path.relative_to(REPOSITORY_ROOT).as_posix()
            if relative not in allowed:
                violations.append(
                    f"{rule.identifier}: unrecorded {rule.description} in {relative}"
                )

    if violations:
        print("Architecture guardrail violations detected:", file=sys.stderr)
        for violation in violations:
            print(f"- {violation}", file=sys.stderr)
        return 1

    print("Architecture guardrails passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
