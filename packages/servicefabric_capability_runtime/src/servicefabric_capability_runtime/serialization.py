"""Stable serialization for optional runtime availability snapshots."""

from __future__ import annotations

import json
from collections.abc import Iterable

from .models import CapabilityAvailability


def serialize_availability_snapshot(records: Iterable[CapabilityAvailability]) -> str:
    """Serialize records in capability-ID order as canonical JSON.

    Availability is a derived view, so serialization is optional and contains
    no process identifiers, endpoints, credentials, or health diagnostics.
    """

    ordered = sorted(
        records,
        key=lambda record: (record.application_id, record.capability_id, record.module_id),
    )
    payload = {"capabilities": [record.to_dict() for record in ordered]}
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
