"""Command dispatcher for the Wave-9 application-factory workflow."""

from __future__ import annotations

from typing import Any

from .application_factory import ApplicationFactoryService


def dispatch_factory(args: Any) -> tuple[int, str, object]:
    service = ApplicationFactoryService.for_current_environment()
    action = args.factory_action
    if action == "plan":
        value = service.plan(
            intent=args.intent,
            blueprint_id=args.blueprint,
            repository=args.repository,
            provider_policy=args.provider_policy,
        )
        return (1 if value["status"] == "blocked" else 0), "factory-plan", value

    run_id = args.run_id
    if action == "approve":
        return 0, "factory-approve", service.approve(run_id, args.decision)
    if action == "bootstrap":
        return 0, "factory-bootstrap", service.bootstrap(run_id)
    if action == "execute":
        return 0, "factory-execute", service.execute(run_id)
    if action == "candidates":
        return 0, "factory-candidates", service.candidates(run_id)
    if action == "review":
        return 0, "factory-review", service.review(run_id, args.task_id, args.decision)
    if action == "integrate":
        handoff = service.integrate(run_id)
        return (0 if handoff.status == "success" else 1), "factory-integrate", handoff
    if action == "status":
        return 0, "factory-status", service.status(run_id)
    if action == "handoff":
        handoff = service.handoff(run_id)
        return (0 if handoff.status == "success" else 1), "factory-handoff", handoff
    raise ValueError(f"unsupported factory command: {action}")


__all__ = ["dispatch_factory"]
