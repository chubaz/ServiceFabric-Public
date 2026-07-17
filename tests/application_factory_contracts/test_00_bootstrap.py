"""Test import bootstrap for Wave-9 shared contracts."""
from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
for relative in (
    "packages/servicefabric_contracts/src",
    "packages/servicefabric_agentic_contracts/src",
    "packages/servicefabric_application_factory_contracts/src",
):
    package_root = str(ROOT / relative)
    if package_root not in sys.path:
        sys.path.insert(0, package_root)
