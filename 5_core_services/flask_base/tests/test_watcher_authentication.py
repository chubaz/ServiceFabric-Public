from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPOSITORY_ROOT / '5_core_services' / 'fabric_watcher'))

import watcher


class WatcherAuthenticationTests(unittest.TestCase):
    @patch('watcher.requests.post')
    def test_enabled_watcher_sends_reload_identity_and_secret(self, post) -> None:
        with patch.object(watcher, 'WATCHER_RELOAD_ENABLED', True), patch.object(
            watcher, 'WATCHER_RELOAD_TOKEN', 'development-reload-secret'
        ), patch.object(watcher, 'WATCHER_SERVICE_ID', 'fabric_watcher'):
            watcher.FabricHandler().trigger_reload(watcher.ShardEvent('approved-service', 'FLASK'))

        self.assertEqual(post.call_args.kwargs['headers'], {
            'X-Service-Identity': 'fabric_watcher',
            'X-Internal-Reload-Token': 'development-reload-secret',
        })

    @patch('watcher.requests.post')
    def test_watcher_does_not_reload_without_a_configured_secret(self, post) -> None:
        with patch.object(watcher, 'WATCHER_RELOAD_ENABLED', True), patch.object(watcher, 'WATCHER_RELOAD_TOKEN', None):
            watcher.FabricHandler().trigger_reload(watcher.ShardEvent('approved-service', 'FLASK'))
        post.assert_not_called()
