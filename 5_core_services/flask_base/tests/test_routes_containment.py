from __future__ import annotations

import io
import sys
import tempfile
import unittest
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
from flask import Flask

FLASK_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(FLASK_ROOT))

from app.routes import core_bp, system_bp


class RouteContainmentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.app = Flask(__name__)
        self.app.config.update(
            TESTING=True,
            DJANGO_SECRET_KEY="test-secret",
            DJANGO_JWT_ALGORITHMS=('HS256',),
            DJANGO_JWT_ISSUER='servicefabric-test',
            DJANGO_JWT_AUDIENCE='servicefabric-test',
            DJANGO_JWT_TOKEN_TYPE='access',
            IS_PRODUCTION=True,
            ENABLE_LEGACY_FAAS_EXECUTION=False,
            ENABLE_INTERNAL_RELOAD=False,
            ENABLE_DEBUG_ROUTES=False,
            INTERNAL_RELOAD_TOKEN=None,
            INTERNAL_RELOAD_ALLOWED_SERVICES=frozenset(),
            INTERNAL_RELOAD_ALLOWED_TARGETS=frozenset(),
            USER_MEDIA_ROOT=self.temporary_directory.name,
            UPLOAD_ALLOWED_EXTENSIONS=frozenset({"txt"}),
            MAX_CONTENT_LENGTH=1024,
        )
        self.app.register_blueprint(core_bp)
        self.app.register_blueprint(system_bp)
        self.client = self.app.test_client()
        self.user_id = uuid.uuid4()
        self.headers = {"Authorization": f"Bearer {self._token(self.user_id)}"}

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def _token(self, user_id):
        return jwt.encode(
            {
                'user_id': str(user_id),
                'token_type': 'access',
                'iss': 'servicefabric-test',
                'aud': 'servicefabric-test',
                'exp': datetime.now(timezone.utc) + timedelta(minutes=5),
                'nbf': datetime.now(timezone.utc) - timedelta(seconds=1),
            },
            'test-secret',
            algorithm='HS256',
        )

    def test_production_execute_route_returns_a_stable_disabled_response(self) -> None:
        response = self.client.post("/execute/123e4567-e89b-12d3-a456-426614174000", headers=self.headers)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.get_json(), {'status': 'disabled', 'message': 'Legacy service execution is disabled'})

    def test_production_reload_and_debug_routes_are_unavailable(self) -> None:
        self.assertEqual(self.client.post('/_internal/reload').status_code, 404)
        self.assertEqual(self.client.get('/_debug_environ').status_code, 404)
        self.assertEqual(self.client.get('/debug/me').status_code, 404)
        self.assertEqual(self.client.get('/debug/me', headers=self.headers).status_code, 404)

    def test_upload_hides_internal_paths_and_prevents_filename_collisions(self) -> None:
        first = self.client.post(
            '/utils/upload',
            headers=self.headers,
            data={'file': (io.BytesIO(b'first'), 'notes.txt')},
            content_type='multipart/form-data',
        )
        second = self.client.post(
            '/utils/upload',
            headers=self.headers,
            data={'file': (io.BytesIO(b'second'), 'notes.txt')},
            content_type='multipart/form-data',
        )
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        first_payload = first.get_json()
        second_payload = second.get_json()
        self.assertNotIn('internal_path', first_payload)
        self.assertNotIn(self.temporary_directory.name, str(first_payload))
        self.assertNotEqual(first_payload['file_id'], second_payload['file_id'])

    def test_upload_file_policy_rejects_disallowed_extensions(self) -> None:
        response = self.client.post(
            '/utils/upload',
            headers=self.headers,
            data={'file': (io.BytesIO(b'unsafe'), 'payload.py')},
            content_type='multipart/form-data',
        )
        self.assertEqual(response.status_code, 400)
        self.assertNotIn(self.temporary_directory.name, response.get_data(as_text=True))

    def test_upload_size_and_tenant_path_are_contained(self) -> None:
        oversized = self.client.post(
            '/utils/upload',
            headers=self.headers,
            data={'file': (io.BytesIO(b'x' * 2048), 'large.txt')},
            content_type='multipart/form-data',
        )
        self.assertEqual(oversized.status_code, 413)
