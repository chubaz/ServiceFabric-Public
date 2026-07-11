"""
Security scan — runs the security-scanner agent against one or all services.
Checks for BOLA, missing auth decorators, path traversal, hardcoded secrets, XSS.
"""
from config import discover_services
from .base import run_agent_task, save_report, run


async def _scan_service(service_name: str) -> str:
    prompt = f"""
Perform a full security scan of the service at `6_service_catalog/{service_name}/`.

Read all Python files in `routes/` and `models.py`, plus all Svelte/TypeScript files in `src/`.

Focus on:
1. BOLA — any DB query missing `owner_id` filter
2. Missing `@token_required` on non-public routes
3. File upload routes — extension validation, path traversal
4. Hardcoded secrets or API keys
5. `{{@html}}` in Svelte without DOMPurify
6. Relative fetch paths missing the `/app/core/{service_name}/api` prefix

Output your findings grouped by CRITICAL / HIGH / MEDIUM / CLEAN as specified in your instructions.
""".strip()

    return await run_agent_task("security-scanner", prompt)


def run_security_scan(service: str | None = None) -> dict[str, str]:
    """
    Run the security scanner.

    Args:
        service: specific service name, or None to scan all services

    Returns:
        dict mapping service_name -> report text
    """
    services = [service] if service else discover_services()
    results  = {}

    for svc in services:
        print(f"  🔍 Scanning {svc}...")
        report = run(_scan_service(svc))
        path   = save_report("security_scan", svc, f"# Security Scan: {svc}\n\n{report}")
        results[svc] = report
        print(f"     → saved to {path.name}")

    return results
