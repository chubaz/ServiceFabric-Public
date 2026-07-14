"""Test import bootstrap for in-repo packages."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for relative in (
    "packages/servicefabric_application_model",
    "packages/servicefabric_framework_kits",
):
    package_root = str(ROOT / relative)
    if package_root not in sys.path:
        sys.path.insert(0, package_root)
