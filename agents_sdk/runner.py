#!/usr/bin/env python3
"""
agents_sdk/runner.py — CLI entry point for on-demand agent tasks.

Usage:
    python runner.py <task> [--service <name>] [--since <git-ref>]
    python runner.py serve  (Starts the WebSocket server on port 9090)

Tasks:
    security_scan       Scan for vulnerabilities (all services or --service)
    code_review         Review recent git changes (or full --service review)
    performance_audit   Find bottlenecks (all services or --service)
    doc_sync            Check CLAUDE.md and scaffolder for staleness
    type_check          Type and lint check (all services or --service)
    full_audit          Run all checks (all services or --service)
    serve               Start WebSocket bridge for browser terminal
"""
import argparse
import sys
import os
import asyncio
import websockets
import json
from pathlib import Path
from dotenv import load_dotenv

# Allow imports from agents_sdk/
sys.path.insert(0, str(Path(__file__).parent))
load_dotenv(Path(__file__).parent.parent / ".env")

from rich.console import Console
from rich.panel   import Panel

# Lazy import to avoid crash if tasks aren't fully configured
try:
    from tasks import TASK_REGISTRY
except ImportError:
    TASK_REGISTRY = {}

console = Console()

async def handle_agent_stream(websocket, path):
    """
    WebSocket handler for the DevFabric Agent terminal.
    Listens for { "cmd": "...", "app_context": "..." } and streams output.
    """
    console.print(f"[bold green]Peer connected:[/] {websocket.remote_address}")
    try:
        async for message in websocket:
            data = json.loads(message)
            cmd = data.get("cmd")
            app_context = data.get("app_context", "core")
            
            # Resolve directory in 6_service_catalog
            # Inside the container, project root is /project
            cwd = Path("/project/6_service_catalog") / app_context
            if not cwd.exists():
                cwd = Path("/project") # fallback to root if app not found

            await websocket.send(f"--- Executing in {cwd} ---")
            
            # Execute command and stream output
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(cwd)
            )

            async def stream_output(stream):
                while True:
                    line = await stream.readline()
                    if not line:
                        break
                    decoded = line.decode().strip()
                    await websocket.send(decoded)

            # Wait for both stdout and stderr
            await asyncio.gather(
                stream_output(process.stdout),
                stream_output(process.stderr)
            )

            await process.wait()
            await websocket.send(f"--- Finished with exit code {process.returncode} ---")

    except websockets.exceptions.ConnectionClosed:
        console.print("[yellow]Peer disconnected.[/]")
    except Exception as e:
        console.print(f"[bold red]Stream Error:[/] {str(e)}")

async def start_websocket_server():
    """Starts the WebSocket server on port 9090."""
    console.print(Panel("[bold green]Starting DevFabric WebSocket Bridge[/]\n[cyan]Listening on ws://0.0.0.0:9090/agent-stream[/]"))
    async with websockets.serve(handle_agent_stream, "0.0.0.0", 9090):
        await asyncio.Future()  # run forever

def main():
    parser = argparse.ArgumentParser(description="Service Fabric Agent SDK runner")
    parser.add_argument("task", help="Task to run (security_scan, code_review, ..., serve)")
    parser.add_argument("--service", default=None, help="Scope to a specific service in 6_service_catalog/")
    parser.add_argument("--since",   default="HEAD~1", help="Git ref for code_review diff (default: HEAD~1)")
    args = parser.parse_args()

    if args.task == "serve":
        asyncio.run(start_websocket_server())
        return

    # Standard task execution logic
    if not os.environ.get("ANTHROPIC_API_KEY"):
        console.print("[bold red]Error:[/] ANTHROPIC_API_KEY is not set.")
        sys.exit(1)

    if args.task not in TASK_REGISTRY:
        console.print(f"[bold red]Error:[/] Unknown task '{args.task}'. Available: {list(TASK_REGISTRY.keys())} + serve")
        sys.exit(1)

    console.print(Panel(f"[bold cyan]Task:[/] {args.task}" +
                        (f"\n[bold cyan]Service:[/] {args.service}" if args.service else ""),
                        title="Service Fabric Agent SDK"))

    task_fn = TASK_REGISTRY[args.task]

    # Call with appropriate kwargs depending on the task
    if args.task == "code_review":
        result = task_fn(service=args.service, since=args.since)
    elif args.task == "doc_sync":
        result = task_fn()
    else:
        result = task_fn(service=args.service)

    console.print("\n[bold green]✓ Done.[/]")

if __name__ == "__main__":
    main()
