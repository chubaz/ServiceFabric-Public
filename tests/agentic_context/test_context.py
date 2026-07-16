import sys
import tempfile
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

PACKAGE_SRC = (
    Path(__file__).resolve().parents[2]
    / "packages"
    / "servicefabric_agentic_context"
    / "src"
)
sys.path.insert(0, str(PACKAGE_SRC))

from servicefabric_agentic_context import build_context_pack


class ContextTests(unittest.TestCase):
    def test_context_is_bounded_and_deterministic(self):
        with tempfile.TemporaryDirectory() as root:
            repository = Path(root)
            (repository / "docs" / "architecture").mkdir(parents=True)
            for relative_path in (
                "README.md",
                "AGENTS.md",
                "workspace.yaml",
                "docs/architecture/specification-map.md",
            ):
                (repository / relative_path).write_text("context", encoding="utf-8")
            (repository / "unrelated.txt").write_text("ignored", encoding="utf-8")

            pack = build_context_pack(
                repository,
                application_id="inventory",
                capability_ids=(capability for capability in ("z", "a", "a")),
            )

            self.assertEqual(pack.repository, str(repository.resolve()))
            self.assertEqual(pack.application_id, "inventory")
            self.assertEqual(
                pack.files,
                (
                    "AGENTS.md",
                    "workspace.yaml",
                    "README.md",
                    "docs/architecture/specification-map.md",
                ),
            )
            self.assertEqual(pack.capability_ids, ("a", "z"))
            with self.assertRaises(FrozenInstanceError):
                pack.application_id = "changed"

    def test_context_excludes_file_symlink_that_escapes_repository(self):
        with tempfile.TemporaryDirectory() as root, tempfile.TemporaryDirectory() as outside:
            repository = Path(root)
            outside_agents = Path(outside, "AGENTS.md")
            outside_agents.write_text("outside", encoding="utf-8")
            (repository / "AGENTS.md").symlink_to(outside_agents)

            pack = build_context_pack(repository)

            self.assertEqual(pack.files, ())

    def test_repository_must_exist_and_be_a_directory(self):
        with tempfile.TemporaryDirectory() as root:
            repository = Path(root)
            missing = repository / "missing"
            regular_file = repository / "file.txt"
            regular_file.write_text("not a repository", encoding="utf-8")

            with self.assertRaises(FileNotFoundError):
                build_context_pack(missing)
            with self.assertRaises(NotADirectoryError):
                build_context_pack(regular_file)

    def test_capability_ids_are_bounded(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaisesRegex(ValueError, "more than 64"):
                build_context_pack(root, capability_ids=(str(index) for index in range(65)))


if __name__ == "__main__":
    unittest.main()
