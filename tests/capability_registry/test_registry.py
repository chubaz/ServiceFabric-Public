from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from servicefabric_capability_registry import (
    CapabilityConflictError,
    CapabilityRegistry,
    CapabilityRegistryError,
    CapabilityNotFoundError,
)


def definition(capability_id: str, application_id: str = "research-notes", summary: str = "Create a note") -> dict:
    return {"capability_id": capability_id, "application_id": application_id, "summary": summary, "operations": ["notes.create"]}


class CapabilityRegistryTests(unittest.TestCase):
    def test_register_is_atomic_and_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            registry = CapabilityRegistry(Path(directory))
            first = registry.register(definition("notes.create"))
            second = registry.register(definition("notes.create"))
            self.assertEqual(first, second)
            self.assertEqual(registry.describe("notes.create"), definition("notes.create"))
            self.assertEqual(len(list(Path(directory).joinpath("capabilities").glob("*.json"))), 1)

    def test_conflict_does_not_replace_existing_definition(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            registry = CapabilityRegistry(Path(directory))
            registry.register(definition("notes.create"))
            with self.assertRaises(CapabilityConflictError):
                registry.register(definition("notes.create", summary="Different"))
            self.assertEqual(registry.describe("notes.create")["summary"], "Create a note")

    def test_list_is_deterministic_and_application_indexed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            registry = CapabilityRegistry(Path(directory))
            registry.register(definition("zeta.read"))
            registry.register(definition("notes.create"))
            registry.register(definition("other.run", application_id="other-app"))
            self.assertEqual([item["capability_id"] for item in registry.list()], ["notes.create", "other.run", "zeta.read"])
            self.assertEqual([item["capability_id"] for item in registry.list("research-notes")], ["notes.create", "zeta.read"])

    def test_digest_is_canonical_and_record_has_integrity_envelope(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            registry = CapabilityRegistry(Path(directory))
            record = registry.register({"application_id": "app", "capability_id": "a", "z": 1, "a": 2})
            path = next(Path(directory).joinpath("capabilities").glob("*.json"))
            envelope = json.loads(path.read_text())
            self.assertEqual(envelope["digest"], record.digest)
            self.assertTrue(record.digest.startswith("sha256:"))

    def test_identifiers_are_path_safe(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            registry = CapabilityRegistry(Path(directory))
            with self.assertRaises(CapabilityRegistryError):
                registry.register(definition("../escape"))
            with self.assertRaises(CapabilityNotFoundError):
                registry.describe("missing")


if __name__ == "__main__":
    unittest.main()
