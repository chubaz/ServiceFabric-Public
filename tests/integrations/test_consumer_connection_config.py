from pathlib import Path
import tempfile
import unittest

from servicefabric_client.config import ServiceFabricConnection


class ConsumerConnectionConfigTests(unittest.TestCase):
 def test_explicit_loopback_connection_configuration(self):
  with tempfile.TemporaryDirectory() as root:
   path=Path(root)/"servicefabric.toml"
   path.write_text('endpoint = "http://127.0.0.1:8765"\ntoolset = "research-demo"\n')
   value=ServiceFabricConnection.load(path)
   self.assertEqual((value.endpoint,value.toolset),("http://127.0.0.1:8765","research-demo"))
