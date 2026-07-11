import unittest
import json
import os
import sys
from pathlib import Path

# Setup paths - ensuring we can find 'app' and our models
base_path = Path("/app") # Inside container path
catalog_path = base_path / 'services_catalog'
sys.path.append(str(catalog_path))

from app import create_app
from app.extensions import db

# Use importlib to avoid hardcoded path issues with the hyphen in 'anki-cards'
import importlib
anki_models = importlib.import_module('anki-cards.models')
AxiomCard = anki_models.AxiomCard
Deck = anki_models.Deck

class TestAnkiCardsMinimal(unittest.TestCase):
    def setUp(self):
        # Create app WITHOUT dynamic blueprint registration if possible
        # Or just use the already created app if it's a singleton
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_api_ping(self):
        """Verify the service is mounted at the expected prefix."""
        # The loader registers it at /anki-cards/
        response = self.client.get('/anki-cards/')
        self.assertIn(response.status_code, [200, 302, 308])

    def test_api_cards_list(self):
        """Test GET /anki-cards/api/cards"""
        response = self.client.get('/anki-cards/api/cards')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIsInstance(data, list)

    def test_api_due_cards(self):
        """Test GET /anki-cards/api/study/due/<deck_id>"""
        deck = Deck.query.first()
        if deck:
            response = self.client.get(f'/anki-cards/api/study/due/{deck.id}')
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertIsInstance(data, list)

if __name__ == '__main__':
    unittest.main()
