from __future__ import annotations

import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


class ComposeContainmentTests(unittest.TestCase):
    def test_watcher_is_defined_only_in_the_development_override(self) -> None:
        base_compose = (REPOSITORY_ROOT / 'docker-compose.yml').read_text(encoding='utf-8')
        development_compose = (REPOSITORY_ROOT / 'docker-compose.dev.yml').read_text(encoding='utf-8')
        production_compose = (REPOSITORY_ROOT / 'docker-compose.prod.yml').read_text(encoding='utf-8')
        self.assertNotIn('fabric_watcher:', base_compose)
        self.assertIn('fabric_watcher:', development_compose)
        self.assertNotIn('fabric_watcher:', production_compose)
