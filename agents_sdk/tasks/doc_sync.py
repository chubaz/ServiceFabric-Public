"""
Documentation sync — runs the documentation-agent to verify CLAUDE.md and
the service-scaffolder agent are still accurate given recent code changes.
"""
import subprocess
from config import PROJECT_ROOT
from .base import run_agent_task, save_report, run


def _get_recent_changes(n_commits: int = 10) -> str:
    result = subprocess.run(
        ["git", "log", f"-{n_commits}", "--oneline"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


async def _sync_docs(recent_commits: str) -> str:
    prompt = f"""
Review the project documentation for accuracy given recent changes.

Recent commits:
{recent_commits}

Steps:
1. Read `CLAUDE.md` in full
2. Read `.claude/agents/service-scaffolder.md` in full
3. Check whether any of the recent commits introduced patterns or commands that are
   not yet documented, or that contradict existing documentation
4. Check if the "after creating files" activation steps in the scaffolder are still accurate
5. Check if any known bugs have been fixed that should update the scaffolder's "Important rules" section

Report specifically what needs to be updated and propose the exact wording changes.
If everything is accurate, say so clearly.
""".strip()

    return await run_agent_task("documentation-agent", prompt)


def run_doc_sync() -> str:
    """
    Check CLAUDE.md and scaffolder for staleness against recent commits.

    Returns:
        Report text
    """
    print("  📝 Checking documentation accuracy...")
    recent = _get_recent_changes(n_commits=20)
    report = run(_sync_docs(recent))
    path   = save_report("doc_sync", None, f"# Documentation Sync Report\n\n{report}")
    print(f"     → saved to {path.name}")
    return report
