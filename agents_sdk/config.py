import os
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
PROJECT_ROOT  = Path(__file__).parent.parent.resolve()
AGENTS_DIR    = PROJECT_ROOT / ".claude" / "agents"
CATALOG_DIR   = PROJECT_ROOT / "6_service_catalog"
REPORTS_DIR   = PROJECT_ROOT / "agents_sdk" / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

# ── Models ─────────────────────────────────────────────────────────────────────
MODEL_OPUS    = "claude-opus-4-6"
MODEL_SONNET  = "claude-sonnet-4-6"
MODEL_HAIKU   = "claude-haiku-4-5-20251001"

# ── Schedules (cron-style via `schedule` library) ──────────────────────────────
SCHEDULE = {
    "security_scan":     {"every": "day",  "at": "02:00"},   # nightly
    "performance_audit": {"every": "week", "at": "monday"},  # weekly
    "code_review":       {"every": "day",  "at": "08:00"},   # morning review of yesterday's commits
    "doc_sync":          {"every": "week", "at": "friday"},  # end-of-week doc check
    "type_check":        {"every": "day",  "at": "07:00"},   # before work
}

def discover_services() -> list[str]:
    """Return all service names from 6_service_catalog/ that have src/main.ts (Svelte)
    or src/main.jsx (React) — i.e. real services, not _shared or node_modules."""
    services = []
    for entry in CATALOG_DIR.iterdir():
        if entry.name.startswith("_") or entry.name.startswith("."):
            continue
        if not entry.is_dir():
            continue
        if (entry / "src" / "main.ts").exists() or (entry / "src" / "main.jsx").exists():
            services.append(entry.name)
    return sorted(services)
