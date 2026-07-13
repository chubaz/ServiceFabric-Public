#!/usr/bin/env python3
"""Register the post-V4 application-platform milestones deterministically."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.agent.common import atomic_json, read_json


TARGETS = (
    (
        "ap-01a-first-hosted-vertical-slice",
        "First hosted vertical slice",
        "current",
        "docs/workplans/milestones/ap-01a-first-hosted-vertical-slice.md",
        "feature/ap-01-first-hosted-vertical-slice",
        "ap-00-modular-framework-kits",
    ),
    (
        "ap-00-modular-framework-kits",
        "Modular framework kits",
        "planned",
        "docs/workplans/milestones/ap-00-modular-framework-kits.md",
        "feature/ap-00-modular-framework-kits",
        "ap-01b-resource-aware-application-hosting",
    ),
    (
        "ap-01b-resource-aware-application-hosting",
        "Resource-aware application hosting",
        "planned",
        "docs/workplans/milestones/ap-01b-resource-aware-application-hosting.md",
        "feature/ap-01b-resource-aware-application-hosting",
        "ap-02-application-capability-connections",
    ),
    (
        "ap-02-application-capability-connections",
        "Application capability connections",
        "planned",
        "docs/workplans/milestones/ap-02-application-capability-connections.md",
        "feature/ap-02-application-capability-connections",
        "",
    ),
)


def entry(identifier: str, title: str, status: str, workplan: str, branch: str, handoff: str) -> dict[str, object]:
    completion = [
        {
            "command": ["python3", "-m", "unittest", "discover", "-s", "tests/ap_01a", "-v"],
            "name": "ap-01a-cli-acceptance",
            "required": True,
            "planned": True,
        }
    ] if identifier == "ap-01a-first-hosted-vertical-slice" else []
    return {
        "allowed_paths": ["clients/python", "packages", "services", "examples", "portfolio", "tests", "docs", "scripts", "config/agent", ".github"],
        "base_branch": "main",
        "context_files": [
            {"path": "AGENTS.md", "reason": "stable repository instructions"},
            {"path": workplan, "reason": "milestone workplan"},
        ],
        "forbidden_paths": ["1_proxy", "2_backend_api/service_fabric/api/migrations", "3_service_templates", "4_generated_services", "5_core_services", "6_service_catalog", "docker-compose.yml", "docker-compose.dev.yml", "docker-compose.prod.yml"],
        "handoff_target": handoff,
        "id": identifier,
        "preflight_checks": ["git", "files", "canonical_hashes", "status"],
        "required_files": ["AGENTS.md", "docs/workplans/current.md", workplan],
        "status": status,
        "suggested_branch": branch,
        "title": title,
        "verification": {
            "completion": completion,
            "readiness": [{"command": ["python3", "scripts/agent/validate_workplans.py"], "name": "workplans", "required": True}],
        },
        "workplan": workplan,
    }


def main() -> int:
    document = read_json("config/agent/milestones.json")
    if set(document) != {"version", "milestones"} or not isinstance(document["milestones"], list):
        raise ValueError("milestone configuration has an unsupported structure")
    identifiers = [item.get("id") for item in document["milestones"]]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("existing milestone configuration contains duplicate IDs")
    requested = {item[0] for item in TARGETS}
    collision = requested.intersection(identifiers)
    if collision:
        raise ValueError("milestone IDs are already registered: " + ", ".join(sorted(collision)))
    for item in document["milestones"]:
        if item["status"] == "current":
            item["status"] = "completed"
    document["milestones"].extend(entry(*item) for item in TARGETS)
    atomic_json("config/agent/milestones.json", document)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
