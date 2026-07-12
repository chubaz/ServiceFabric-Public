#!/usr/bin/env python3
"""Export deterministic ServiceFabric contract schemas and representative examples."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_SOURCE = REPOSITORY_ROOT / "packages" / "servicefabric_contracts" / "src"
sys.path.insert(0, str(PACKAGE_SOURCE))

from servicefabric_contracts.schema_export import write_schema_snapshot  # noqa: E402


EXAMPLES = {
    "frontend_only_svelte.json": "frontend-only-svelte.json",
    "cli_financial_calculator.json": "cli-financial-calculator.json",
    "managed_http_capsule.json": "managed-http-capsule.json",
    "external_http_provider.json": "external-http-provider.json",
    "federated_external_mcp.json": "federated-external-mcp.json",
    "graph_backed_research.json": "graph-backed-research.json",
    "worker_only_reconciliation.json": "worker-only-reconciliation.json",
    "tool_definition_math_calculate.json": "tool-definition-math-calculate.json",
    "tool_revision_math_calculate_v1.json": "tool-revision-math-calculate-v1.json",
    "tool_definition_research_search_papers.json": "tool-definition-research-search-papers.json",
    "tool_revision_research_search_papers_v1.json": "tool-revision-research-search-papers-v1.json",
    "tool_definition_project_create_task.json": "tool-definition-project-create-task.json",
    "tool_revision_project_create_task_v1.json": "tool-revision-project-create-task-v1.json",
    "tool_deployment_math_calculate.json": "tool-deployment-math-calculate.json",
    "tool_status_math_calculate.json": "tool-status-math-calculate.json",
    "invocation_math_calculate.json": "invocation-math-calculate.json",
    "result_math_calculate_success.json": "result-math-calculate-success.json",
    "invocation_research_search_papers.json": "invocation-research-search-papers.json",
    "result_research_search_papers_partial.json": "result-research-search-papers-partial.json",
    "invocation_project_create_task.json": "invocation-project-create-task.json",
    "result_project_create_task_success.json": "result-project-create-task-success.json",
    "result_project_create_task_error.json": "result-project-create-task-error.json",
    "effect_receipt_project_create_task.json": "effect-receipt-project-create-task.json",
    "operation_research_search_papers.json": "operation-research-search-papers.json",
    "translated/translation_report_quant_vite.json": "legacy-translation-quant-composite-report.json",
}


def export(output: Path) -> None:
    write_schema_snapshot(output)
    examples = output / "examples"
    examples.mkdir(parents=True, exist_ok=True)
    fixtures = REPOSITORY_ROOT / "packages" / "servicefabric_contracts" / "tests" / "fixtures"
    for source_name, target_name in EXAMPLES.items():
        shutil.copyfile(fixtures / source_name, examples / target_name)


if __name__ == "__main__":
    export(REPOSITORY_ROOT / "schemas" / "servicefabric" / "v1alpha1")
