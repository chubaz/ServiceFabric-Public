"""
Shared utilities for all tasks.
"""
import asyncio
import datetime
from pathlib import Path

from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, TextBlock

from config import PROJECT_ROOT, REPORTS_DIR
from agent_loader import load_agent, AgentSpec


async def run_agent_task(
    agent_name: str,
    prompt: str,
    extra_tools: list[str] | None = None,
    permission_mode: str = "default",
) -> str:
    """
    Load an agent definition from .claude/agents/, run it against `prompt`,
    and return the full text response.

    Args:
        agent_name:      Name matching a .claude/agents/<name>.md file
        prompt:          The task prompt passed to the agent
        extra_tools:     Additional tools beyond what the agent definition specifies
        permission_mode: "default" | "acceptEdits" | "bypassPermissions"
    """
    spec = load_agent(agent_name)
    tools = list(set(spec.tools + (extra_tools or [])))

    options = ClaudeAgentOptions(
        system_prompt    = spec.system_prompt,
        allowed_tools    = tools,
        permission_mode  = permission_mode,
        cwd              = str(PROJECT_ROOT),
        model            = spec.model,
    )

    output_parts: list[str] = []

    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    output_parts.append(block.text)

    return "\n".join(output_parts)


def save_report(task_name: str, service: str | None, content: str) -> Path:
    """Write a report to agents_sdk/reports/ and return its path."""
    ts    = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    slug  = f"{task_name}_{service}_{ts}" if service else f"{task_name}_{ts}"
    path  = REPORTS_DIR / f"{slug}.md"
    path.write_text(content)
    return path


def run(coro):
    """Convenience wrapper to run an async task from sync context."""
    return asyncio.run(coro)
