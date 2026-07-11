"""
Loads .claude/agents/*.md files and extracts their system prompts + metadata.
This keeps the agent markdown files as the single source of truth —
the SDK just reads them at runtime rather than duplicating their content.
"""
import re
from pathlib import Path
from dataclasses import dataclass
from agents_sdk.config import AGENTS_DIR, MODEL_SONNET


@dataclass
class AgentSpec:
    name: str
    description: str
    system_prompt: str
    model: str
    tools: list[str]


_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_FIELD_RE       = re.compile(r"^(\w+):\s*(.+)$", re.MULTILINE)


def load_agent(name: str) -> AgentSpec:
    """Parse a .claude/agents/<name>.md file into an AgentSpec."""
    path = AGENTS_DIR / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Agent definition not found: {path}")

    raw = path.read_text()

    # Extract YAML frontmatter
    fm_match = _FRONTMATTER_RE.match(raw)
    if not fm_match:
        raise ValueError(f"No frontmatter found in {path}")

    fm_text       = fm_match.group(1)
    system_prompt = raw[fm_match.end():].strip()
    fields        = dict(_FIELD_RE.findall(fm_text))

    # Parse tools list (comma-separated or YAML list)
    tools_raw = fields.get("tools", "Read, Glob, Grep")
    tools = [t.strip() for t in tools_raw.split(",") if t.strip()]

    return AgentSpec(
        name          = name,
        description   = fields.get("description", ""),
        system_prompt = system_prompt,
        model         = fields.get("model", MODEL_SONNET),
        tools         = tools,
    )
