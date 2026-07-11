"""
Code review — runs the code-reviewer agent on recently changed files (git diff)
or on a specific service.
"""
import subprocess
from config import PROJECT_ROOT, discover_services
from .base import run_agent_task, save_report, run


def _get_changed_files(since: str = "HEAD~1") -> list[str]:
    """Return list of changed files relative to project root since the given git ref."""
    result = subprocess.run(
        ["git", "diff", "--name-only", since],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    return [f for f in result.stdout.strip().splitlines() if f]


async def _review_files(files: list[str], context: str) -> str:
    file_list = "\n".join(f"- `{f}`" for f in files)
    prompt = f"""
Review the following changed files for correctness, Service Fabric conventions, and common bugs.

Changed files:
{file_list}

Read each file in full before reviewing it.

For each file apply the full review checklist from your instructions:
- Flask routes: owner_id filtering, @token_required, error shapes
- SQLAlchemy models: owner_id, srv_ prefix, extend_existing
- Svelte: Svelte 5 runes, API_BASE with leading slash, editorOpen state, app.css present
- main.ts: ROOT_ID matches template, mount/unmount pattern

Context: {context}
""".strip()

    return await run_agent_task("code-reviewer", prompt)


async def _review_service(service_name: str) -> str:
    prompt = f"""
Review all source files in `6_service_catalog/{service_name}/`:
- `models.py`
- All files in `routes/`
- All `.svelte` and `.ts` files in `src/`
- `src/main.ts`

Apply the full review checklist from your instructions.
Report findings grouped by CRITICAL / WARNING / INFO / OK.
""".strip()

    return await run_agent_task("code-reviewer", prompt)


def run_code_review(service: str | None = None, since: str = "HEAD~1") -> dict[str, str]:
    """
    Run the code reviewer.

    Args:
        service: specific service to review fully, or None to review recent git changes
        since:   git ref for diff when no service is specified (default: last commit)

    Returns:
        dict mapping label -> report text
    """
    results = {}

    if service:
        print(f"  📋 Reviewing service: {service}...")
        report = run(_review_service(service))
        path   = save_report("code_review", service, f"# Code Review: {service}\n\n{report}")
        results[service] = report
        print(f"     → saved to {path.name}")
    else:
        changed = _get_changed_files(since)
        if not changed:
            print("  📋 No changed files found.")
            return {}

        # Group by service
        service_files: dict[str, list[str]] = {}
        for f in changed:
            parts = f.split("/")
            if len(parts) >= 2 and parts[0] == "6_service_catalog":
                svc = parts[1]
                service_files.setdefault(svc, []).append(f)
            else:
                service_files.setdefault("_core", []).append(f)

        for svc, files in service_files.items():
            print(f"  📋 Reviewing {len(files)} changed file(s) in {svc}...")
            report = run(_review_files(files, context=f"git diff since {since}"))
            path   = save_report("code_review", svc, f"# Code Review: {svc} (git diff)\n\n{report}")
            results[svc] = report
            print(f"     → saved to {path.name}")

    return results
