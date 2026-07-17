"""Test import bootstrap for the Wave-9 blueprint compiler."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for relative in (
    "packages/servicefabric_contracts/src",
    "packages/servicefabric_agentic_contracts/src",
    "packages/servicefabric_agentic_planner/src",
    "packages/servicefabric_application_factory_contracts/src",
    "packages/servicefabric_application_model",
    "packages/servicefabric_framework_kits",
    "packages/servicefabric_blueprints",
    "packages/servicefabric_engineering_blueprints/src",
):
    package_root = str(ROOT / relative)
    if package_root not in sys.path:
        sys.path.insert(0, package_root)
