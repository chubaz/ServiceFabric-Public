from __future__ import annotations

import sys
import unittest
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
from flask import Flask, jsonify, g

FLASK_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(FLASK_ROOT))

from app.middleware import token_required


class TokenClaimTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.update(
            TESTING=True,
            DJANGO_SECRET_KEY='test-secret',
            DJANGO_JWT_ALGORITHMS=('HS256',),
            DJANGO_JWT_ISSUER='https://identity.example.test',
            DJANGO_JWT_AUDIENCE='servicefabric-test',
            DJANGO_JWT_TOKEN_TYPE='access',
        )

        @self.app.get('/protected')
        @token_required
        def protected():
            return jsonify({'user_id': str(g.user_id)})

        self.client = self.app.test_client()
        self.user_id = uuid.uuid4()

    def issue_token(self, **overrides):
        claims = {
            'user_id': str(self.user_id),
            'token_type': 'access',
            'iss': self.app.config['DJANGO_JWT_ISSUER'],
            'aud': self.app.config['DJANGO_JWT_AUDIENCE'],
            'exp': datetime.now(timezone.utc) + timedelta(minutes=5),
            'nbf': datetime.now(timezone.utc) - timedelta(seconds=1),
        }
        claims.update(overrides)
        return jwt.encode(claims, 'test-secret', algorithm='HS256')

    def request_with(self, token):
        return self.client.get('/protected', headers={'Authorization': f'Bearer {token}'})

    def test_valid_django_claims_produce_a_uuid_identity(self):
        response = self.request_with(self.issue_token())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()['user_id'], str(self.user_id))

    def test_invalid_issuer_audience_or_token_type_are_rejected(self):
        for claims in (
            {'iss': 'https://other.example.test'},
            {'aud': 'other-audience'},
            {'token_type': 'refresh'},
        ):
            response = self.request_with(self.issue_token(**claims))
            self.assertEqual(response.status_code, 401)
            self.assertEqual(response.get_json(), {'message': 'Invalid or missing credentials'})

    def test_missing_or_malformed_user_identity_is_rejected(self):
        missing = self.issue_token()
        payload = jwt.decode(missing, 'test-secret', algorithms=['HS256'], options={'verify_signature': True, 'verify_exp': False, 'verify_aud': False})
        del payload['user_id']
        missing_identity = jwt.encode(payload, 'test-secret', algorithm='HS256')

        for token in (missing_identity, self.issue_token(user_id='not-a-uuid')):
            self.assertEqual(self.request_with(token).status_code, 401)

    def test_expired_and_not_before_tokens_are_rejected(self):
        self.assertEqual(self.request_with(self.issue_token(exp=0)).status_code, 401)
        self.assertEqual(
            self.request_with(self.issue_token(nbf=datetime.now(timezone.utc) + timedelta(minutes=1))).status_code,
            401,
        )
