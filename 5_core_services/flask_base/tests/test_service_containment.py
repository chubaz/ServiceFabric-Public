from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from flask import Flask

FLASK_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(FLASK_ROOT))

from app.service_security import ServiceAccessDenied, resolve_service_directory, validate_identifier
from app.services_loader import LegacyExecutionDisabled, register_all_services, run_script_for_instance


class FakeApp:
    def __init__(self, config):
        self.config = config
        self.blueprints = {}

        class Logger:
            def info(self, *args, **kwargs):
                pass

            def warning(self, *args, **kwargs):
                pass

            def exception(self, *args, **kwargs):
                pass

        self.logger = Logger()

    def register_blueprint(self, blueprint, url_prefix):
        self.blueprints[blueprint.name] = blueprint


class ServiceContainmentTests(unittest.TestCase):
    def test_path_traversal_identifiers_are_rejected(self) -> None:
        for value in ("../outside", "service/child", "service.module", "", "_private"):
            with self.assertRaises(ServiceAccessDenied):
                validate_identifier(value)

    def test_resolved_service_path_cannot_escape_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            with self.assertRaises(ServiceAccessDenied):
                resolve_service_directory(root, "../outside")

    def test_production_never_scans_generated_services(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            catalogue = root / "catalogue"
            generated = root / "generated"
            catalogue.mkdir()
            generated.mkdir()
            (generated / "mutable").mkdir()
            (generated / "mutable" / "__init__.py").write_text("raise RuntimeError('must not import')")
            app = FakeApp({
                "SERVICE_CATALOG_PATH": str(catalogue),
                "SERVICE_GENERATED_PATH": str(generated),
                "ENABLE_DYNAMIC_SERVICE_IMPORTS": True,
                "ENABLE_GENERATED_SERVICE_IMPORTS": True,
                "IS_PRODUCTION": True,
                "LEGACY_CATALOG_ALLOWLIST": frozenset(),
            })
            register_all_services(app)
            self.assertNotIn("dynamic_sandbox.mutable", sys.modules)

    def test_production_catalogue_requires_an_explicit_allowlist(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            catalogue = root / "catalogue"
            catalogue.mkdir()
            (catalogue / "unapproved").mkdir()
            (catalogue / "unapproved" / "__init__.py").write_text("raise RuntimeError('must not import')")
            app = FakeApp({
                "SERVICE_CATALOG_PATH": str(catalogue),
                "SERVICE_GENERATED_PATH": str(root / "generated"),
                "ENABLE_DYNAMIC_SERVICE_IMPORTS": True,
                "ENABLE_GENERATED_SERVICE_IMPORTS": False,
                "IS_PRODUCTION": True,
                "LEGACY_CATALOG_ALLOWLIST": frozenset(),
            })
            register_all_services(app)
            self.assertNotIn("dynamic_catalog.unapproved", sys.modules)

    def test_faas_execution_is_disabled_without_its_explicit_flag(self) -> None:
        class Instance:
            service_type = "approved"

        app = Flask(__name__)
        app.config.update(IS_PRODUCTION=True, ENABLE_LEGACY_FAAS_EXECUTION=False)
        with app.test_request_context('/'):
            with self.assertRaises(LegacyExecutionDisabled):
                run_script_for_instance(Instance(), {})
