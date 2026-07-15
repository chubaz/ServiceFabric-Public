import tempfile
import unittest
from pathlib import Path

from servicefabric_application_generator import (
    GenerationCollision, GenerationRequest, InvalidGenerationParameter, ApplicationGenerator,
)
from servicefabric_blueprints import TEXT_UTILITY_BLUEPRINT


class GeneratorTests(unittest.TestCase):
    def test_materialization_is_deterministic_and_generates_source(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            generator = ApplicationGenerator()
            args = ("sample-app", "Sample App", TEXT_UTILITY_BLUEPRINT)
            a = generator.generate(GenerationRequest(*args, Path(first)))
            b = generator.generate(GenerationRequest(*args, Path(second)))
            self.assertEqual(a.files, b.files)
            self.assertEqual((a.root / "modules/text-api/module.yaml").read_bytes(), (b.root / "modules/text-api/module.yaml").read_bytes())
            self.assertTrue((a.root / "modules/text-api/app.py").is_file())

    def test_collision_does_not_modify_existing_target(self):
        with tempfile.TemporaryDirectory() as root:
            target = Path(root) / "sample-app"
            target.mkdir()
            marker = target / "keep.txt"
            marker.write_text("keep", encoding="utf-8")
            with self.assertRaises(GenerationCollision):
                ApplicationGenerator().generate(GenerationRequest("sample-app", "Sample", TEXT_UTILITY_BLUEPRINT, Path(root)))
            self.assertEqual(marker.read_text(encoding="utf-8"), "keep")

    def test_missing_parameter_is_rejected_before_writing(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(InvalidGenerationParameter):
                ApplicationGenerator().generate(GenerationRequest("sample-app", "Sample", TEXT_UTILITY_BLUEPRINT, Path(root), {"bad/": "x"}))
            self.assertFalse((Path(root) / "sample-app").exists())
