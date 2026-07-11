"""
Performance audit — runs the performance-analyzer agent against one or all services.
Checks for N+1 queries, missing indexes, unbounded queries, reactive loops in Svelte.
"""
from config import discover_services
from .base import run_agent_task, save_report, run


async def _audit_service(service_name: str) -> str:
    prompt = f"""
Perform a performance audit of `6_service_catalog/{service_name}/`.

Read:
- `models.py` — check for missing indexes on filtered columns
- All files in `routes/` — check for N+1 queries, unbounded `.all()`, repeated queries per request
- All `.svelte` files in `src/` — check for reactive loops in `$effect`, redundant fetches, large list rendering

Estimate the impact of each issue as HIGH / MEDIUM / LOW.
Output your findings in the format specified in your instructions.
""".strip()

    return await run_agent_task("performance-analyzer", prompt)


def run_performance_audit(service: str | None = None) -> dict[str, str]:
    """
    Run the performance analyzer.

    Args:
        service: specific service name, or None to audit all services

    Returns:
        dict mapping service_name -> report text
    """
    services = [service] if service else discover_services()
    results  = {}

    for svc in services:
        print(f"  ⚡ Auditing {svc}...")
        report = run(_audit_service(svc))
        path   = save_report("performance_audit", svc, f"# Performance Audit: {svc}\n\n{report}")
        results[svc] = report
        print(f"     → saved to {path.name}")

    return results
