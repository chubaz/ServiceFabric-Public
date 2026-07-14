"""Unit and integration tests for primitive compatibility constraints."""

from __future__ import annotations

import unittest

from servicefabric_application_model import load_module_definition_from_dict
from servicefabric_framework_kits import PrimitiveMismatch, get_default_catalog


class TestPrimitiveCompatibility(unittest.TestCase):
    def test_fastapi_service_kit_compatibility_with_service_primitive(self) -> None:
        catalog = get_default_catalog()

        # Valid configuration: service primitive + fastapi-service kit
        valid_module = load_module_definition_from_dict({
            "apiVersion": "servicefabric.local/v1",
            "kind": "ApplicationModule",
            "metadata": {"id": "notes-api", "version": "1.0.0"},
            "spec": {
                "primitive": "service",
                "kit": (
                    "fastapi-service @ServiceFabric/portfolio/applications/"
                    "revisions/examples.hello-static-1.0.0.json"
                ),
                "source": "modules/api",
            }
        })
        # Must pass validation without raising PrimitiveMismatch
        catalog.validate_module(valid_module)

    def test_reject_fastapi_service_kit_with_incompatible_primitive(self) -> None:
        catalog = get_default_catalog()

        # Invalid configuration: web primitive + fastapi-service kit
        invalid_module = load_module_definition_from_dict({
            "apiVersion": "servicefabric.local/v1",
            "kind": "ApplicationModule",
            "metadata": {"id": "notes-frontend", "version": "1.0.0"},
            "spec": {
                "primitive": "web",  # incompatible primitive for fastapi-service
                "kit": (
                    "fastapi-service @ServiceFabric/portfolio/applications/"
                    "revisions/examples.hello-static-1.0.0.json"
                ),
                "source": "modules/frontend",
            }
        })

        # Validating an incompatible primitive / kit configuration must raise PrimitiveMismatch
        with self.assertRaises(PrimitiveMismatch):
            catalog.validate_module(invalid_module)


if __name__ == "__main__":
    unittest.main()
