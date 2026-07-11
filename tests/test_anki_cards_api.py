import unittest
import json
import os
import sys
from pathlib import Path

# Setup paths
base_path = Path("/Users/lorenzocc/Desktop/8. Programming/ServiceFabric/service-fabric-project")
catalog_path = base_path / '6_service_catalog'
sys.path.append(str(catalog_path))

from app import create_app
from app.extensions import db
import importlib
anki_models = importlib.import_module('anki-cards.models')
Course = anki_models.Course
Module = anki_models.Module
Topic = anki_models.Topic
Deck = anki_models.Deck
SubDeck = anki_models.SubDeck
AxiomCard = anki_models.AxiomCard
CardReviewHistory = anki_models.CardReviewHistory

class TestAnkiCardsAPI(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_api_cards_get(self):
        """Test GET /anki-cards/api/cards"""
        response = self.client.get('/anki-cards/api/cards')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIsInstance(data, list)

    def test_api_due_cards(self):
        """Test GET /anki-cards/api/study/due/<deck_id>"""
        # Get first deck
        deck = Deck.query.first()
        if deck:
            response = self.client.get(f'/anki-cards/api/study/due/{deck.id}')
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertIsInstance(data, list)

    def test_api_review_card(self):
        """Test POST /anki-cards/api/study/review/<card_id>"""
        card = AxiomCard.query.first()
        if card:
            response = self.client.post(
                f'/anki-cards/api/study/review/{card.id}',
                data=json.dumps({'rating': 3, 'duration': 10}),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertEqual(data['status'], 'updated')

if __name__ == '__main__':
    unittest.main()
