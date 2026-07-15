from __future__ import annotations

import json
from typing import Any


def canonical_json(value: Any) -> str:
    """Return the stable JSON representation used for operation manifests."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def serialize_operation_definition(operation: Any) -> str:
    return canonical_json(operation.to_dict())
