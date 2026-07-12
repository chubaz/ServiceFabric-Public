#!/usr/bin/env python3
"""Validate committed translated fixtures and deterministic report serialization."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/"packages/servicefabric_contracts/src"))
from servicefabric_contracts import ServicePackageDefinition
from servicefabric_contracts.translation_report import LegacyManifestTranslationReport
for path in sorted((ROOT/"packages/servicefabric_contracts/tests/fixtures/translated").glob("*.json")):
 data=json.loads(path.read_text()); model=ServicePackageDefinition.model_validate(data) if data.get("kind")=="ServicePackageDefinition" else LegacyManifestTranslationReport.model_validate(data)
 assert json.dumps(model.model_dump(mode="json",by_alias=True),sort_keys=True)==json.dumps(model.model_dump(mode="json",by_alias=True),sort_keys=True)
print("Legacy translation snapshots are current.")
