"""
Full audit — runs all checks (security, performance, types, code review) on
every service. Intended for nightly runs or pre-deploy checks.
Produces a single consolidated report.
"""
import datetime
from config import discover_services, REPORTS_DIR
from .security_scan     import run_security_scan
from .performance_audit import run_performance_audit
from .type_check        import run_type_check
from .code_review       import run_code_review
from .doc_sync          import run_doc_sync


def run_full_audit(service: str | None = None) -> str:
    """
    Run every check. If `service` is provided, scope the audit to that service only.

    Returns:
        Path string of the consolidated report file.
    """
    services  = [service] if service else discover_services()
    ts        = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    sections  = [f"# Full Audit Report\n\nGenerated: {ts}\nServices: {', '.join(services)}\n"]

    print(f"\n🚀 Starting full audit across {len(services)} service(s)...\n")

    # ── Security ──────────────────────────────────────────────────────────────
    print("── Security Scan ─────────────────────────────")
    sec_results = run_security_scan(service)
    sections.append("## Security Scan\n")
    for svc, report in sec_results.items():
        sections.append(f"### {svc}\n\n{report}\n")

    # ── Performance ───────────────────────────────────────────────────────────
    print("\n── Performance Audit ─────────────────────────")
    perf_results = run_performance_audit(service)
    sections.append("## Performance Audit\n")
    for svc, report in perf_results.items():
        sections.append(f"### {svc}\n\n{report}\n")

    # ── Types / Lint ──────────────────────────────────────────────────────────
    print("\n── Type / Lint Check ─────────────────────────")
    type_results = run_type_check(service)
    sections.append("## Type / Lint Check\n")
    for svc, report in type_results.items():
        sections.append(f"### {svc}\n\n{report}\n")

    # ── Code Review (full service review, not diff) ────────────────────────────
    print("\n── Code Review ───────────────────────────────")
    for svc in services:
        review_results = run_code_review(service=svc)
        sections.append("## Code Review\n")
        for label, report in review_results.items():
            sections.append(f"### {label}\n\n{report}\n")

    # ── Documentation ─────────────────────────────────────────────────────────
    print("\n── Documentation Sync ────────────────────────")
    doc_report = run_doc_sync()
    sections.append(f"## Documentation Sync\n\n{doc_report}\n")

    # ── Write consolidated report ──────────────────────────────────────────────
    slug = f"full_audit_{service}_" if service else "full_audit_"
    slug += datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = REPORTS_DIR / f"{slug}.md"
    path.write_text("\n".join(sections))

    print(f"\n✅ Full audit complete → {path}")
    return str(path)
