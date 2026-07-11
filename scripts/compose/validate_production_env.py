#!/usr/bin/env python3
"""Fail closed when the production Compose environment is incomplete or templated."""

from __future__ import annotations

import sys
from pathlib import Path


REQUIRED = {
    "PROXY_PORT",
    "ALLOWED_HOSTS",
    "SECRET_KEY",
    "DJANGO_SECRET_KEY",
    "POSTGRES_DB",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "DATABASE_URL",
    "JWT_SECRET_KEY",
    "JWT_ISSUER",
    "JWT_AUDIENCE",
    "CORS_ALLOWED_ORIGINS",
}
PLACEHOLDER_MARKERS = ("change_me", "replace_", "yourdomain.com", "example.com")


def parse_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key] = value
    return values


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: validate_production_env.py PATH", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    if not path.is_file():
        print("Production environment file is missing", file=sys.stderr)
        return 1
    values = parse_env(path)
    invalid = sorted(
        key for key in REQUIRED
        if not values.get(key) or any(marker in values[key].lower() for marker in PLACEHOLDER_MARKERS)
    )
    if invalid:
        print("Production environment contains missing or placeholder values: " + ", ".join(invalid), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
