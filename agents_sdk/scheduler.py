#!/usr/bin/env python3
"""
agents_sdk/scheduler.py — Runs agent tasks on a schedule.

Reads SCHEDULE from config.py and registers jobs using the `schedule` library.
Intended to run as a persistent Docker service or a cron-launched process.

Usage:
    python scheduler.py                # run the scheduler loop
    python scheduler.py --run-now      # run all tasks immediately, then exit
"""
import sys
import os
import time
import argparse
import logging
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent))
load_dotenv(Path(__file__).parent.parent / ".env.dev")

import schedule
from rich.console import Console

from config import SCHEDULE
from tasks  import TASK_REGISTRY

console = Console()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("scheduler")


def _safe_run(task_name: str, **kwargs):
    """Run a task and log any exceptions without crashing the scheduler."""
    try:
        log.info(f"Starting scheduled task: {task_name}")
        console.print(f"\n[bold cyan]⏰ Scheduled:[/] {task_name}")
        TASK_REGISTRY[task_name](**kwargs)
        log.info(f"Completed: {task_name}")
    except Exception as e:
        log.error(f"Task {task_name} failed: {e}", exc_info=True)
        console.print(f"[bold red]✗ {task_name} failed:[/] {e}")


def register_jobs():
    """Register all jobs from config.SCHEDULE."""
    cfg = SCHEDULE

    # Security scan — nightly
    schedule.every().day.at(cfg["security_scan"]["at"]).do(
        _safe_run, "security_scan"
    )

    # Performance audit — weekly Monday
    schedule.every().monday.do(
        _safe_run, "performance_audit"
    )

    # Code review — review yesterday's commits each morning
    schedule.every().day.at(cfg["code_review"]["at"]).do(
        _safe_run, "code_review", since="HEAD~5"
    )

    # Doc sync — Friday afternoons
    schedule.every().friday.at(cfg["doc_sync"]["at"]).do(
        _safe_run, "doc_sync"
    )

    # Type check — daily before work
    schedule.every().day.at(cfg["type_check"]["at"]).do(
        _safe_run, "type_check"
    )

    log.info("Scheduler registered. Jobs:")
    for job in schedule.get_jobs():
        log.info(f"  {job}")


def main():
    parser = argparse.ArgumentParser(description="Service Fabric Agent Scheduler")
    parser.add_argument("--run-now", action="store_true",
                        help="Run all tasks immediately and exit")
    args = parser.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        console.print("[bold red]Error:[/] ANTHROPIC_API_KEY is not set.")
        sys.exit(1)

    if args.run_now:
        console.print("[bold yellow]Running all tasks immediately...[/]")
        for name, fn in TASK_REGISTRY.items():
            if name == "full_audit":
                continue  # skip — it calls the others
            _safe_run(name)
        console.print("[bold green]✓ All tasks complete.[/]")
        return

    console.print("[bold green]Service Fabric Agent Scheduler starting...[/]")
    register_jobs()
    console.print("Waiting for scheduled tasks. Press Ctrl+C to stop.\n")

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
