"""Acceptance and adversarial fixtures owned by the Research Notes application."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOMAIN = ROOT / "examples" / "research-notes" / "domain"
API = ROOT / "examples" / "research-notes" / "api"
sys.path[:0] = [
    str(ROOT / "packages" / "servicefabric_application_model"),
    str(ROOT / "packages" / "servicefabric_framework_kits"),
    str(DOMAIN),
    str(API),
]

from research_notes_domain import NoteNotFound, NotesService, SQLiteNoteRepository, ValidationError
from servicefabric_framework_kits import get_default_catalog, parse_kit_reference


class ResearchNotesPersistenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database = Path(self.temporary_directory.name) / "notes.sqlite3"

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def service(self) -> NotesService:
        service = NotesService(SQLiteNoteRepository(f"sqlite:///{self.database}"))
        service.initialize()
        return service

    def test_note_persists_after_a_new_service_instance(self) -> None:
        created = self.service().create(title="Gateway design", body="Applications expose selected actions.")

        restored = self.service().get(created.id)

        self.assertEqual(restored.title, "Gateway design")
        self.assertEqual(restored.body, "Applications expose selected actions.")

    def test_search_is_case_insensitive_and_does_not_use_sql_wildcards(self) -> None:
        service = self.service()
        service.create(title="Gateway design", body="An interface boundary.")
        service.create(title="Unrelated", body="A different record.")

        results = service.search("GATEWAY")

        self.assertEqual([note.title for note in results], ["Gateway design"])
        self.assertEqual(service.search("%' OR 1=1 --"), [])

    def test_rejects_blank_fields_and_missing_notes(self) -> None:
        service = self.service()

        with self.assertRaises(ValidationError):
            service.create(title="   ", body="body")
        with self.assertRaises(ValidationError):
            service.create(title="title", body="   ")
        with self.assertRaises(NoteNotFound):
            service.get(999)


class ResearchNotesFixtureTests(unittest.TestCase):
    def test_each_module_kit_reference_parses_and_resolves_from_the_default_catalog(self) -> None:
        expected_kits = {
            "api": ("fastapi-service", "service"),
            "web": ("react-web", "web"),
            "domain": ("python-library", "library"),
        }
        catalog = get_default_catalog()

        for module, (kit_id, primitive) in expected_kits.items():
            manifest = ROOT / "examples" / "research-notes" / module / "module.yaml"
            kit_reference = next(
                line.strip().removeprefix("kit: ")
                for line in manifest.read_text(encoding="utf-8").splitlines()
                if line.strip().startswith("kit:")
            )

            parsed = parse_kit_reference(kit_reference)
            definition, _ = catalog.resolve(parsed)

            self.assertEqual(parsed.kit_id, kit_id)
            self.assertEqual(parsed.version, "1.0.0")
            self.assertEqual(definition.primitive, primitive)

    def test_modules_are_declared_as_an_ordinary_library_service_and_web_app(self) -> None:
        application = (ROOT / "examples" / "research-notes" / "application.yaml").read_text(encoding="utf-8")
        api_manifest = (API / "module.yaml").read_text(encoding="utf-8")
        web_source = (ROOT / "examples" / "research-notes" / "web" / "app.js").read_text(encoding="utf-8")

        self.assertIn("id: notes-domain", application)
        self.assertIn("id: notes-api", application)
        self.assertIn("id: notes-web", application)
        self.assertIn("type: sqlite", api_manifest)
        self.assertIn("/health/ready", api_manifest)
        self.assertIn("/notes", web_source)


if __name__ == "__main__":
    unittest.main()
