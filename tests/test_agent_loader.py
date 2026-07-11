import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
import sys
import os

# Add the project root to sys.path to import agents_sdk
sys.path.append(os.getcwd())

from agents_sdk.agent_loader import load_agent

class TestAgentLoader(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.agents_dir_path = Path(self.test_dir.name)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_load_agent_success(self):
        agent_name = "test-agent"
        agent_content = "---\ndescription: A test agent\nmodel: claude-sonnet\ntools: Read, Write\n---\n\nThis is the system prompt."

        agent_file = self.agents_dir_path / f"{agent_name}.md"
        agent_file.write_text(agent_content)

        with patch("agents_sdk.agent_loader.AGENTS_DIR", self.agents_dir_path):
            spec = load_agent(agent_name)

        self.assertEqual(spec.name, agent_name)
        self.assertEqual(spec.description, "A test agent")
        self.assertEqual(spec.model, "claude-sonnet")
        self.assertEqual(spec.tools, ["Read", "Write"])
        self.assertEqual(spec.system_prompt, "This is the system prompt.")

    def test_load_agent_file_not_found(self):
        with patch("agents_sdk.agent_loader.AGENTS_DIR", self.agents_dir_path):
            with self.assertRaises(FileNotFoundError):
                load_agent("non-existent-agent")

    def test_load_agent_no_frontmatter(self):
        agent_name = "no-frontmatter"
        agent_content = "This is just a system prompt without frontmatter."

        agent_file = self.agents_dir_path / f"{agent_name}.md"
        agent_file.write_text(agent_content)

        with patch("agents_sdk.agent_loader.AGENTS_DIR", self.agents_dir_path):
            with self.assertRaises(ValueError) as cm:
                load_agent(agent_name)
            self.assertIn("No frontmatter found", str(cm.exception))

    def test_load_agent_defaults(self):
        agent_name = "default-agent"
        # Minimum valid frontmatter
        agent_content = "---\ndescription: Default description\n---\n\nSystem prompt only."

        agent_file = self.agents_dir_path / f"{agent_name}.md"
        agent_file.write_text(agent_content)

        with patch("agents_sdk.agent_loader.AGENTS_DIR", self.agents_dir_path):
            spec = load_agent(agent_name)

        self.assertEqual(spec.name, agent_name)
        self.assertEqual(spec.description, "Default description")
        # Default model from config
        from agents_sdk.config import MODEL_SONNET
        self.assertEqual(spec.model, MODEL_SONNET)
        # Default tools
        self.assertEqual(spec.tools, ["Read", "Glob", "Grep"])
        self.assertEqual(spec.system_prompt, "System prompt only.")

    def test_load_agent_tools_comma_separated(self):
        agent_name = "tools-comma"
        agent_content = "---\ntools: Tool1, Tool2, Tool3\n---\n\nPrompt"

        agent_file = self.agents_dir_path / f"{agent_name}.md"
        agent_file.write_text(agent_content)

        with patch("agents_sdk.agent_loader.AGENTS_DIR", self.agents_dir_path):
            spec = load_agent(agent_name)

        self.assertEqual(spec.tools, ["Tool1", "Tool2", "Tool3"])

if __name__ == "__main__":
    unittest.main()
