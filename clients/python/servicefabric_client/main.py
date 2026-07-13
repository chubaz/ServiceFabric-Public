"""Local-only ServiceFabric developer composition root and command dispatcher."""
from __future__ import annotations

import argparse
import json
import os
import shlex
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from servicefabric_artifacts import FileArtifactStore
from servicefabric_builder import ApplicationPortfolio, StaticWebBuilder, artifact_manifest, validate_source
from servicefabric_contracts import ToolInvocationRequest
from servicefabric_contracts.budgets import ExecutionBudget
from servicefabric_contracts.caller import CallerContext
from servicefabric_contracts.effects import EffectDeclaration
from servicefabric_contracts.governance import AuthorityGrant
from servicefabric_contracts.metadata import OwnerReference, ResourceMetadata
from servicefabric_contracts.permissions import PermissionRequirement
from servicefabric_contracts.protocol import ProtocolContext
from servicefabric_contracts.invocation import RevisionInvocationTarget
from servicefabric_governance import ApprovalService, GovernedInvocationBoundary, InvocationGovernanceProfile, PolicyBundle, VersionedPolicyEvaluator
from servicefabric_operations import DurableOperationStore, IdempotencyRepository
from servicefabric_runtime import FilePortfolio, InvocationKernel
from servicefabric_runtime.portfolio import __file__ as _portfolio_module


VERSION = "0.1.0a1"
POLICY_DIGEST = "sha256:" + "a" * 64
MCP_PROFILE = "2025-11-25"


def workspace_path() -> Path:
    return Path(os.environ.get("SERVICEFABRIC_HOME", Path.cwd() / ".servicefabric")).expanduser().resolve()


def json_output(value: object) -> str:
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json", by_alias=True)
    return json.dumps(value, sort_keys=True, indent=2) + "\n"


class LocalRuntime:
    def __init__(self, home: Path):
        self.home = home
        self.artifacts = FileArtifactStore(home / "artifacts")
        self.operations = DurableOperationStore(home / "operations")
        self.idempotency = IdempotencyRepository(home / "idempotency")
        portfolio_root = Path(_portfolio_module).resolve().parent.parent / "portfolios"
        self.portfolio = FilePortfolio(portfolio_root)
        self.kernel = InvocationKernel(self.portfolio)
        self.caller = CallerContext(subject_ref="local-developer", principal_type="human", tenant_ref="local", issuer="servicefabric-local", scopes=("math-calculate",), authentication_strength="multi_factor")
        bundle = PolicyBundle(bundle_id="local-policy", version="1.0.0", digest=POLICY_DIGEST, allowed_scopes=("math-calculate",))
        profile = InvocationGovernanceProfile("math.calculate", "1.0.0", (EffectDeclaration(effect_type="none", target_category="calculation", scope="local", reversibility="not_applicable", verification_required=False, approval_required=False, idempotency_required=False),), (PermissionRequirement(permission_id="math-calculate", tenant_scope="caller_tenant", resource_scope="local"),), AuthorityGrant(scopes=("math-calculate",), tenant_ref="local"), ExecutionBudget(), "low", "local-policy", "1.0.0", POLICY_DIGEST)
        self.governed = GovernedInvocationBoundary(evaluator=VersionedPolicyEvaluator((bundle,)), approvals=ApprovalService(), runtime=self.kernel, profiles=(profile,))
        repo = Path(__file__).resolve().parents[3]
        self.applications = LocalApplications(ApplicationPortfolio(repo / "portfolio" / "applications"), self.artifacts)

    def invoke_math(self, arguments: dict[str, object]):
        request_id = "local-request-" + uuid4().hex[:16]
        request = ToolInvocationRequest(apiVersion="servicefabric.ai/v1alpha1", kind="ToolInvocationRequest", metadata=ResourceMetadata(id=request_id, name="Local invocation", description="Local developer request.", owner_ref=OwnerReference(kind="service", id="servicefabric-cli")), spec={"request_id": request_id, "target": RevisionInvocationTarget(target_kind="revision", tool_id="math.calculate", revision_ref="1.0.0"), "arguments": arguments, "caller_context": self.caller, "protocol_context": ProtocolContext(protocol="internal", adapter_ref="trusted-local-cli"), "budget": ExecutionBudget(), "requested_response_mode": "synchronous"})
        result = self.governed.invoke(request, trusted_adapter_ref="trusted-local-cli", now=datetime.now(timezone.utc))
        return request, result


class LocalApplications:
    """Local adapter over existing application portfolio, builder, and artifact store."""
    def __init__(self, portfolio: ApplicationPortfolio, store: FileArtifactStore):
        self.portfolio, self.store = portfolio, store

    def list_applications(self):
        return tuple(sorted(path.stem for path in (self.portfolio.root / "definitions").glob("*.json")))

    def describe_application(self, application_id: str):
        return self.portfolio.definition(application_id)

    def build(self, application_id: str, revision: str):
        revision_model = self.portfolio.revision(application_id, revision)
        source = validate_source(self.portfolio.source_root(revision_model.spec.source_bundle_ref), self.portfolio.verify_source(revision_model))
        with tempfile.TemporaryDirectory(prefix="servicefabric-local-build-") as temporary:
            output = StaticWebBuilder().build(revision_model, source, Path(temporary) / "output")
            manifest = artifact_manifest(revision_model, output, StaticWebBuilder())
            self.store.put_artifact(manifest, output.output_root)
        return {"application_id": application_id, "revision": revision, "artifact_digest": manifest.spec.artifact_digest, "status": "success"}


def require_workspace(home: Path) -> None:
    if not (home / "workspace.json").is_file():
        raise ValueError("workspace is not initialized; run 'servicefabric init'")


def init_workspace(home: Path) -> dict[str, object]:
    for name in ("operations", "idempotency", "artifacts", "approvals", "config"):
        (home / name).mkdir(parents=True, exist_ok=True)
    marker = home / "workspace.json"
    if not marker.exists():
        marker.write_text(json.dumps({"format": 1, "policy_bundle": "local-policy@1.0.0", "mcp_profile": MCP_PROFILE}, sort_keys=True) + "\n", encoding="utf-8")
    return {"workspace": str(home), "initialized": True, "local_only": True}


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="servicefabric", description="ServiceFabric local developer command")
    root.add_argument("--json", action="store_true")
    root.add_argument("--debug", action="store_true")
    root.add_argument("--verbose", action="store_true")
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("init"); commands.add_parser("status"); commands.add_parser("doctor"); commands.add_parser("shell")
    tools = commands.add_parser("tools").add_subparsers(dest="action", required=True); tools.add_parser("list"); describe = tools.add_parser("describe"); describe.add_argument("tool_id")
    invoke = commands.add_parser("invoke"); invoke.add_argument("tool_id"); source = invoke.add_mutually_exclusive_group(required=True); source.add_argument("--arguments"); source.add_argument("--arguments-file"); invoke.add_argument("--explain", action="store_true")
    apps = commands.add_parser("apps").add_subparsers(dest="action", required=True); apps.add_parser("list"); app = apps.add_parser("describe"); app.add_argument("application_id"); build = apps.add_parser("build"); build.add_argument("application_id"); build.add_argument("--revision", required=True)
    artifacts = commands.add_parser("artifacts").add_subparsers(dest="action", required=True); artifact = artifacts.add_parser("describe"); artifact.add_argument("digest"); artifact = artifacts.add_parser("verify"); artifact.add_argument("digest")
    return root


def dispatch(argv: list[str]) -> tuple[int, object]:
    args = parser().parse_args(argv)
    home = workspace_path()
    if args.command == "init": return 0, init_workspace(home)
    if args.command == "shell": return 0, {"shell": True}
    require_workspace(home)
    runtime = LocalRuntime(home)
    if args.command == "status": return 0, {"workspace": str(home), "version": VERSION, "services": ["runtime", "governance", "operations", "application-builder", "artifact-store"], "policy_bundle": "local-policy@1.0.0", "tools": 1, "applications": len(runtime.applications.list_applications()), "operations": len(list((home / "operations").glob("*.json"))), "mcp_profile": MCP_PROFILE, "limitations": "local-only; no public transport or production identity"}
    if args.command == "doctor": return 0, {"python": sys.version.split()[0], "workspace": str(home), "policy_bundle": "available", "portfolio": "available", "operation_store": "readable", "artifact_store": "readable", "mcp_profile": MCP_PROFILE}
    if args.command == "tools":
        if args.action == "list": return 0, {"tools": [{"tool_id": "math.calculate", "revision": "1.0.0", "description": "Deterministic arithmetic calculation."}]}
        if args.tool_id != "math.calculate": raise ValueError("tool not found")
        return 0, {"tool_id": "math.calculate", "revision": "1.0.0", "machine_callable": True, "effects": ["none"]}
    if args.command == "invoke":
        if args.tool_id != "math.calculate": raise ValueError("tool not found")
        raw = Path(args.arguments_file).read_text(encoding="utf-8") if args.arguments_file else args.arguments
        try: arguments = json.loads(raw)
        except json.JSONDecodeError as error: raise ValueError("arguments must be valid JSON") from error
        request, result = runtime.invoke_math(arguments)
        value = {"request_id": request.spec.request_id, "revision": "1.0.0", "policy_outcome": "allow", "effective_authority": ["math-calculate"], "effective_budget": request.spec.budget.model_dump(mode="json"), "result": result.model_dump(mode="json", by_alias=True)}
        if args.explain: value["explain"] = ["resolved tool revision", "constructed canonical request", "evaluated policy", "applied effective authority and budget", "selected synchronous path", "projected result"]
        return 0, value
    if args.command == "apps":
        if args.action == "list": return 0, {"applications": list(runtime.applications.list_applications())}
        if args.action == "describe": return 0, runtime.applications.describe_application(args.application_id)
        caller = runtime.caller
        return 0, runtime.applications.build(args.application_id, args.revision)
    if args.command == "artifacts":
        if args.action == "describe": return 0, runtime.artifacts.get_manifest(args.digest)
        verification = runtime.artifacts.verify_artifact(args.digest)
        return 0, verification.__dict__
    raise ValueError("unsupported command")


def main(argv: list[str] | None = None) -> int:
    try:
        selected = sys.argv[1:] if argv is None else argv
        if selected == ["shell"]:
            print("ServiceFabric local developer shell")
            print(f"workspace: {workspace_path()}")
            while True:
                try: line = input("sf> ").strip()
                except EOFError: break
                if line in {"exit", "quit"}: break
                if not line: continue
                code, value = dispatch(shlex.split(line)); print(json_output(value), end="")
            return 0
        code, value = dispatch(selected)
        print(json_output(value), end="")
        return code
    except argparse.ArgumentError as error:
        print(f"error: {error}", file=sys.stderr); return 2
    except Exception as error:
        debug = "--debug" in (sys.argv[1:] if argv is None else argv)
        if debug: raise
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
