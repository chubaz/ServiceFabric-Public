import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/"clients/python"),str(ROOT/"services/tool_runtime")]
from servicefabric_client.cli import arguments
class ClientTests(unittest.TestCase):
 def test_cli_is_bounded(self):self.assertEqual(arguments(["math.calculate","--expression","2+2"])["arguments"]["expression"],"2+2")
