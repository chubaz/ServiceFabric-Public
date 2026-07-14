"""Unit and integration tests for the reviewed FrameworkKitCatalog."""

from __future__ import annotations

import unittest

from servicefabric_application_model import load_module_definition_from_dict, ValidationError
from servicefabric_framework_kits import (
    DuplicateKitRegistration,
    FrameworkKitCatalog,
    FrameworkKitDefinition,
    KitNotFound,
    KitReference,
    get_default_catalog,
    PrimitiveMismatch,
)
from servicefabric_framework_kits.fastapi_service.adapter import FastAPIServiceAdapter
from servicefabric_framework_kits.python_library.adapter import PythonLibraryAdapter
from servicefabric_framework_kits.react_web.adapter import ReactWebAdapter


class TestKitCatalog(unittest.TestCase):
    def test_default_catalog_registration(self) -> None:
        catalog = get_default_catalog()
        ref = KitReference(kit_id="fastapi-service", version="1.0.0")
        
        definition, adapter = catalog.resolve(ref)
        self.assertEqual(definition.reference.kit_id, "fastapi-service")
        self.assertEqual(definition.primitive, "service")
        self.assertIsInstance(adapter, FastAPIServiceAdapter)

    def test_reject_duplicate_registration(self) -> None:
        catalog = FrameworkKitCatalog()
        ref = KitReference(kit_id="custom-kit", version="1.0.0")
        definition = FrameworkKitDefinition(
            reference=ref,
            primitive="service",
            adapter_id="custom-adapter",
            runtime_family="python",
            development_supported=True,
            build_supported=True,
            runtime_supported=True,
        )
        adapter = FastAPIServiceAdapter()

        catalog.register(definition, adapter)
        
        # Registering the identical kit reference again must raise DuplicateKitRegistration
        with self.assertRaises(DuplicateKitRegistration):
            catalog.register(definition, adapter)

    def test_default_catalog_registers_all_reviewed_kit_primitives(self) -> None:
        catalog = get_default_catalog()

        react_definition, react_adapter = catalog.resolve(
            KitReference(kit_id="react-web", version="1.0.0")
        )
        library_definition, library_adapter = catalog.resolve(
            KitReference(kit_id="python-library", version="1.0.0")
        )

        self.assertEqual(react_definition.primitive, "web")
        self.assertIsInstance(react_adapter, ReactWebAdapter)
        self.assertEqual(library_definition.primitive, "library")
        self.assertIsInstance(library_adapter, PythonLibraryAdapter)

    def test_reject_unknown_kit_reference(self) -> None:
        catalog = FrameworkKitCatalog()
        ref = KitReference(kit_id="unknown-kit", version="2.0.0")
        
        with self.assertRaises(KitNotFound):
            catalog.resolve(ref)


if __name__ == "__main__":
    unittest.main()
