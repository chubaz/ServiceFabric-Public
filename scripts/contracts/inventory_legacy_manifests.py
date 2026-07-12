#!/usr/bin/env python3
"""Create or verify the deterministic repository legacy-manifest inventory."""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/"packages/servicefabric_contracts/src"))
from servicefabric_contracts.legacy_manifest import parse_legacy_manifest, placeholders
from servicefabric_contracts.translation_profiles import TEMPLATE_PROFILE
OUT=ROOT/"docs/refactoring/legacy-manifest-inventory.json"
ROOTS=(ROOT/"3_service_templates",ROOT/"6_service_catalog")
def inventory():
 rows=[]
 for root in ROOTS:
  for path in sorted(root.rglob("fabric-manifest.json")):
   if path.is_symlink() or root.resolve() not in path.resolve().parents: continue
   data=path.read_bytes(); row={"path":path.relative_to(ROOT).as_posix(),"sha256":hashlib.sha256(data).hexdigest()}
   try:
    manifest=parse_legacy_manifest(data); profile=TEMPLATE_PROFILE.get(manifest.template)
    row.update(parse_status="valid",template=manifest.template,placeholders=list(placeholders(manifest)),recommended_profile=profile.value if profile else "assessment_only")
   except Exception: row.update(parse_status="invalid",template=None,placeholders=[],recommended_profile="assessment_only")
   rows.append(row)
 return {"manifest_count":len(rows),"manifests":rows}
def canonical(value): return json.dumps(value,indent=2,sort_keys=True)+"\n"
if __name__=="__main__":
 parser=argparse.ArgumentParser(); parser.add_argument("--check",action="store_true"); args=parser.parse_args(); content=canonical(inventory())
 if args.check:
  if not OUT.exists() or OUT.read_text()!=content: raise SystemExit("Legacy manifest inventory snapshot is stale")
  print("Legacy manifest inventory snapshot is current.")
 else: OUT.write_text(content,encoding="utf-8")
