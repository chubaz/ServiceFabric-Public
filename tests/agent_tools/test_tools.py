import tempfile
import unittest
from servicefabric_agent_tools import BoundedAgentTools
class ToolTests(unittest.TestCase):
 def test_outside_path_is_blocked(self):
  with tempfile.TemporaryDirectory() as root: self.assertEqual(BoundedAgentTools(root).invoke("workspace.inspect",{"path":"../outside"}).status,"blocked")
