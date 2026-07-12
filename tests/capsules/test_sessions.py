from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from servicefabric_capsules.sessions import CapsuleSessionManager


class CapsuleSessionLifecycleTests(unittest.TestCase):
    def test_session_expiration_and_close_are_bounded(self) -> None:
        opened = datetime(2026, 7, 12, 10, 0, tzinfo=timezone.utc)
        manager = CapsuleSessionManager(opened, opened + timedelta(seconds=10), 10, 2)
        self.assertTrue(manager.can_serve(opened))
        manager.record_request(opened)
        self.assertEqual(manager.requests_served, 1)
        self.assertTrue(manager.can_serve(opened + timedelta(seconds=5)))
        self.assertFalse(manager.can_serve(opened + timedelta(seconds=11)))
        manager.close()
        self.assertTrue(manager.closed)
        self.assertEqual(manager.status, "closed")
