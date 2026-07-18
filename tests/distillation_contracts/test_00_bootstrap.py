"""Import bootstrap for Wave-10 shared-contract tests."""
from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
for relative in (
    "packages/servicefabric_contracts/src",
    "packages/servicefabric_capability_model/src",
    "packages/servicefabric_distillation_contracts/src",
):
    package_root = str(ROOT / relative)
    if package_root not in sys.path:
        sys.path.insert(0, package_root)
