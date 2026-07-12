#!/usr/bin/env python3
"""Fail when committed contract schema snapshots differ from deterministic export."""

from __future__ import annotations

import filecmp
import sys
import tempfile
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT / "packages" / "servicefabric_contracts" / "src"))

from export_schemas import export  # noqa: E402


def main() -> int:
    committed = REPOSITORY_ROOT / "schemas" / "servicefabric" / "v1alpha1"
    with tempfile.TemporaryDirectory(prefix="servicefabric-contract-schemas-") as temporary:
        generated = Path(temporary) / "v1alpha1"
        export(generated)
        expected = sorted(path.relative_to(committed) for path in committed.rglob("*") if path.is_file())
        actual = sorted(path.relative_to(generated) for path in generated.rglob("*") if path.is_file())
        if expected != actual:
            print("Contract schema snapshot file set is stale.", file=sys.stderr)
            return 1
        for relative in expected:
            if not filecmp.cmp(committed / relative, generated / relative, shallow=False):
                print(f"Contract schema snapshot is stale: {relative}", file=sys.stderr)
                return 1
    print("Contract schema snapshots are current.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
