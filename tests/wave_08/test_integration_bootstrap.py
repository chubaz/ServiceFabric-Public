import json
from pathlib import Path
import tempfile
import unittest

from servicefabric_client.agent_providers import ProviderRegistry, load_provider_policy


class Wave08IntegrationBootstrapTests(unittest.TestCase):
    def test_registry_is_static_and_policy_has_no_credentials(self) -> None:
        self.assertEqual([item["provider_id"] for item in ProviderRegistry().list()], ["claude", "codex", "gemini", "pi"])
        with tempfile.TemporaryDirectory() as temporary:
            policy = Path(temporary) / "policy.json"
            policy.write_text(json.dumps({"default_provider": "codex", "maximum_parallel_per_provider": 1, "timeout_seconds": 60}), encoding="utf-8")
            self.assertEqual(load_provider_policy(policy).default_provider, "codex")
