"""Command-line interface for local foundation-release checks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .doctor import run_doctor


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="servicefabric")
    subcommands = parser.add_subparsers(dest="command", required=True)
    doctor = subcommands.add_parser("doctor", help="validate local foundation-release prerequisites")
    doctor.add_argument("--repository-root", type=Path, default=Path.cwd())
    doctor.add_argument("--json", action="store_true", help="emit a machine-readable report")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command != "doctor":  # pragma: no cover - argparse owns this guard.
        return 2
    report = run_doctor(args.repository_root)
    if args.json:
        print(json.dumps(report.as_dict(), indent=2, sort_keys=True))
    else:
        print(f"ServiceFabric {report.release}: {'healthy' if report.ok else 'attention required'}")
        for check in report.checks:
            print(f"[{check.status.upper()}] {check.name}: {check.detail}")
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
