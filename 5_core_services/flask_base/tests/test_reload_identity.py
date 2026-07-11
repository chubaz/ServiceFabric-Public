from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from flask import Flask

FLASK_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(FLASK_ROOT))

from app.routes import system_bp


class ReloadIdentityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = Flask(__name__)
        self.app.config.update(
            TESTING=True,
            IS_PRODUCTION=False,
            ENABLE_INTERNAL_RELOAD=True,
            INTERNAL_RELOAD_TOKEN='development-reload-secret',
            INTERNAL_RELOAD_ALLOWED_SERVICES=frozenset({'fabric_watcher'}),
            INTERNAL_RELOAD_ALLOWED_TARGETS=frozenset({'approved-service'}),
        )
        self.app.register_blueprint(system_bp)
        self.client = self.app.test_client()

    def test_public_callers_cannot_reload_services(self) -> None:
        response = self.client.post('/_internal/reload', json={'target': 'approved-service'})
        self.assertEqual(response.status_code, 403)

    def test_reload_requires_an_allowlisted_target(self) -> None:
        response = self.client.post(
            '/_internal/reload',
            json={'target': 'other-service'},
            headers={
                'X-Service-Identity': 'fabric_watcher',
                'X-Internal-Reload-Token': 'development-reload-secret',
            },
        )
        self.assertEqual(response.status_code, 403)

    @patch('app.routes.threading.Thread')
    def test_allowlisted_service_identity_can_request_reload(self, thread_class) -> None:
        response = self.client.post(
            '/_internal/reload',
            json={'target': 'approved-service'},
            headers={
                'X-Service-Identity': 'fabric_watcher',
                'X-Internal-Reload-Token': 'development-reload-secret',
            },
        )
        self.assertEqual(response.status_code, 202)
        thread_class.return_value.start.assert_called_once()
