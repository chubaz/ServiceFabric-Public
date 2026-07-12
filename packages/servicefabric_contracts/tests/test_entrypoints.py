from __future__ import annotations

import unittest

from pydantic import ValidationError

from servicefabric_contracts.entrypoints import EntrypointDeclaration


class EntrypointTests(unittest.TestCase):
    def test_none_exposure_cannot_be_combined(self) -> None:
        with self.assertRaises(ValidationError):
            EntrypointDeclaration.model_validate({"id": "worker", "kind": "worker", "description": "Worker", "runtime_ref": "container:worker", "machine_callable": False, "may_produce_effects": False, "exposures": [{"kind": "none"}, {"kind": "web"}]})

    def test_mcp_requires_operation_reference(self) -> None:
        with self.assertRaises(ValidationError):
            EntrypointDeclaration.model_validate({"id": "server", "kind": "mcp_server", "description": "MCP", "runtime_ref": "external:mcp", "machine_callable": True, "may_produce_effects": False, "exposures": [{"kind": "mcp"}]})
