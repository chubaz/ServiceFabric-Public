"""
Type and lint check — runs the type-lint-checker agent on one or all services.
Also attempts to run svelte-check via docker if available.
"""
import subprocess
from config import PROJECT_ROOT, discover_services
from .base import run_agent_task, save_report, run


def _run_svelte_check(service_name: str) -> str:
    """Run svelte-check inside the vite container and return stdout."""
    result = subprocess.run(
        [
            "docker-compose", "exec", "-T", "core_vite_service",
            "npx", "svelte-check",
            "--workspace", f"/app/services_catalog/{service_name}/src",
            "--output", "human",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    return (result.stdout + result.stderr).strip()


async def _check_service(service_name: str, svelte_output: str) -> str:
    svelte_section = (
        f"svelte-check output:\n```\n{svelte_output}\n```\n\n"
        if svelte_output
        else "svelte-check was not available.\n\n"
    )

    prompt = f"""
Perform a type and lint check on `6_service_catalog/{service_name}/`.

{svelte_section}
Additionally, read all `.svelte` and `.ts` files in `src/` and all Python files in `routes/` and `models.py`.

Check for:
1. Untyped `$state` variables — should have explicit generic types
2. `catch (e: any)` — suggest `unknown`
3. Svelte 4 patterns mixed into Svelte 5 files (`writable`, `onMount`, `$:` reactive statements)
4. Dynamic Tailwind f-string classes (`bg-{{color}}-400`) — should use lookup maps
5. `API_BASE` defined as `const` with leading slash
6. SQLAlchemy UUID columns compared to integers
7. Inconsistent API response shapes across routes

Output findings as Errors / Warnings / Info / Clean as specified in your instructions.
""".strip()

    return await run_agent_task("type-lint-checker", prompt)


def run_type_check(service: str | None = None) -> dict[str, str]:
    """
    Run the type/lint checker.

    Args:
        service: specific service name, or None to check all services

    Returns:
        dict mapping service_name -> report text
    """
    services = [service] if service else discover_services()
    results  = {}

    for svc in services:
        print(f"  🔎 Type-checking {svc}...")

        # Try running svelte-check via docker (non-fatal if unavailable)
        svelte_out = ""
        try:
            svelte_out = _run_svelte_check(svc)
        except Exception:
            pass

        report = run(_check_service(svc, svelte_out))
        path   = save_report("type_check", svc, f"# Type/Lint Check: {svc}\n\n{report}")
        results[svc] = report
        print(f"     → saved to {path.name}")

    return results
