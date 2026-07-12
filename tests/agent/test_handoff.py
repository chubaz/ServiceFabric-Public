import unittest
from scripts.agent.prepare_handoff import PROMPT
class HandoffTests(unittest.TestCase):
 def test_prompt_is_short_and_secret_free(self): self.assertLessEqual(len(PROMPT.split()),100);self.assertNotIn("password",PROMPT.lower())
