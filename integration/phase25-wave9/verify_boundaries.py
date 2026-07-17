"""Keep Wave-9 integration focused on composition and shared contracts."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
manifest = ROOT / "config/agents/wave-09/wave.yaml"
text = manifest.read_text(encoding="utf-8")
if "draft" in text or "implementation_authorized: false" in text:
    raise SystemExit("Wave-9 manifest must not retain draft-only authorization")
if not (ROOT / "packages/servicefabric_application_factory_contracts").is_dir():
    raise SystemExit("Wave-9 shared factory contracts are required")
print("Wave-9 integration boundaries passed.")
