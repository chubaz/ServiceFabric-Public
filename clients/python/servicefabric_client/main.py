"""Local-only ServiceFabric developer composition root and command dispatcher."""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from servicefabric_application_builder import create_application_builder_service
from servicefabric_artifacts import FileArtifactStore
from servicefabric_capsule_host import create_capsule_host_service
from servicefabric_contracts import ApplicationBuildRequest, ToolInvocationRequest
from servicefabric_contracts import CapsuleHostRequest
from servicefabric_contracts.budgets import ExecutionBudget
from servicefabric_contracts.caller import CallerContext
from servicefabric_contracts.effects import EffectDeclaration
from servicefabric_contracts.governance import AuthorityGrant
from servicefabric_contracts.invocation import RevisionInvocationTarget
from servicefabric_contracts.metadata import OwnerReference, ResourceMetadata
from servicefabric_contracts.permissions import PermissionRequirement
from servicefabric_contracts.protocol import ProtocolContext
from servicefabric_governance import (
    ApprovalService,
    GovernedInvocationBoundary,
    InvocationGovernanceProfile,
    PolicyBundle,
    VersionedPolicyEvaluator,
)
from servicefabric_mcp_gateway import McpGatewayService
from servicefabric_mcp_projection import (
    DiscoveryService,
    McpCallRequest,
    McpClientCapabilities,
    ProjectionCandidate,
    ProjectedMcpTool,
    SessionManager,
    TrustedMcpTransportContext,
)
from servicefabric_operations import DurableOperationStore, IdempotencyRepository
from servicefabric_runtime import FilePortfolio, InvocationKernel
from servicefabric_runtime.portfolio import __file__ as _portfolio_module
from servicefabric_tool_runtime_service import ToolRuntimeService

from .capsules import CapsuleClient
from .mcp import McpGatewayClient


VERSION = "0.1.0a1"
POLICY_DIGEST = "sha256:" + "a" * 64
MCP_PROFILE = "2025-11-25"


class CliUsageError(ValueError):
    """A concise command-line validation error."""


class ServiceFabricArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise CliUsageError(message)


def workspace_path() -> Path:
    value = os.environ.get("SERVICEFABRIC_HOME", Path.cwd() / ".servicefabric")
    return Path(value).expanduser().resolve()


def as_json_value(value: Any) -> Any:
    """Convert contract and service values into deterministic JSON-compatible data."""
    if hasattr(value, "model_dump"):
        return as_json_value(value.model_dump(mode="json", by_alias=True))
    if dataclasses.is_dataclass(value):
        return as_json_value(dataclasses.asdict(value))
    if isinstance(value, dict):
        return {str(key): as_json_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [as_json_value(item) for item in value]
    return value


def json_output(value: object) -> str:
    return json.dumps(as_json_value(value), sort_keys=True, indent=2) + "\n"


def _display_workspace(home: Path) -> str:
    try:
        return str(home.relative_to(Path.cwd()))
    except ValueError:
        return str(home)


class LocalRuntime:
    """Composes reviewed local services; command handlers do not execute tools directly."""

    def __init__(self, home: Path):
        self.home = home
        self.artifacts = FileArtifactStore(home / "artifacts")
        self.operations = DurableOperationStore(home / "operations")
        self.idempotency = IdempotencyRepository(home / "idempotency")
        portfolio_root = Path(_portfolio_module).resolve().parent.parent / "portfolios"
        self.portfolio = FilePortfolio(portfolio_root)
        self.runtime_service = ToolRuntimeService(InvocationKernel(self.portfolio))
        self.caller = CallerContext(
            subject_ref="local-developer",
            principal_type="human",
            tenant_ref="local",
            issuer="servicefabric-local",
            scopes=("math-calculate",),
            authentication_strength="multi_factor",
        )
        bundle = PolicyBundle(
            bundle_id="local-policy",
            version="1.0.0",
            digest=POLICY_DIGEST,
            allowed_scopes=("math-calculate",),
        )
        profile = InvocationGovernanceProfile(
            "math.calculate",
            "1.0.0",
            (
                EffectDeclaration(
                    effect_type="none",
                    target_category="calculation",
                    scope="local",
                    reversibility="not_applicable",
                    verification_required=False,
                    approval_required=False,
                    idempotency_required=False,
                ),
            ),
            (
                PermissionRequirement(
                    permission_id="math-calculate",
                    tenant_scope="caller_tenant",
                    resource_scope="local",
                ),
            ),
            AuthorityGrant(scopes=("math-calculate",), tenant_ref="local"),
            ExecutionBudget(),
            "low",
            "local-policy",
            "1.0.0",
            POLICY_DIGEST,
        )
        self.governed = GovernedInvocationBoundary(
            evaluator=VersionedPolicyEvaluator((bundle,)),
            approvals=ApprovalService(),
            runtime=self.runtime_service,
            profiles=(profile,),
        )
        repository = Path(__file__).resolve().parents[3]
        self.applications = create_application_builder_service(
            portfolio_root=repository / "portfolio" / "applications",
            artifact_store_root=home / "artifacts",
        )
        self.capsules = CapsuleClient(
            create_capsule_host_service(
                capsule_portfolio_root=repository / "portfolio" / "capsules",
                application_portfolio_root=repository / "portfolio" / "applications",
                artifact_store_root=home / "artifacts",
            )
        )
        candidate = ProjectionCandidate(
            canonical_tool_id="math.calculate",
            revision_ref="1.0.0",
            name="math.calculate",
            title="Calculate",
            description="Deterministic arithmetic calculation.",
            input_schema={
                "type": "object",
                "properties": {"expression": {"type": "string"}},
                "required": ["expression"],
                "additionalProperties": False,
            },
            enabled=True,
            available=True,
            discover_scopes=("math-calculate",),
            structured_result=True,
        )
        projected_tool = ProjectedMcpTool(
            name=candidate.name,
            canonical_tool_id=candidate.canonical_tool_id,
            revision_ref=candidate.revision_ref,
            title=candidate.title,
            description=candidate.description,
            input_schema=candidate.input_schema,
            structured_result=candidate.structured_result,
        )
        self.mcp = McpGatewayClient(
            McpGatewayService(
                sessions=SessionManager(),
                discovery=DiscoveryService((candidate,)),
                tools=(projected_tool,),
                governed_invocations=self.governed,
                operations=self.operations,
            )
        )

    def invoke_math(self, arguments: dict[str, object]):
        request_id = "local-request-" + uuid4().hex[:16]
        request = ToolInvocationRequest(
            apiVersion="servicefabric.ai/v1alpha1",
            kind="ToolInvocationRequest",
            metadata=ResourceMetadata(
                id=request_id,
                name="Local invocation",
                description="Local developer request.",
                owner_ref=OwnerReference(kind="service", id="servicefabric-cli"),
            ),
            spec={
                "request_id": request_id,
                "target": RevisionInvocationTarget(
                    target_kind="revision",
                    tool_id="math.calculate",
                    revision_ref="1.0.0",
                ),
                "arguments": arguments,
                "caller_context": self.caller,
                "protocol_context": ProtocolContext(
                    protocol="internal", adapter_ref="trusted-local-cli"
                ),
                "budget": ExecutionBudget(),
                "requested_response_mode": "synchronous",
            },
        )
        result = self.governed.invoke(
            request,
            trusted_adapter_ref="trusted-local-cli",
            now=datetime.now(timezone.utc),
        )
        return request, result


def require_workspace(home: Path) -> None:
    if not (home / "workspace.json").is_file():
        raise ValueError("workspace is not initialized. Run 'servicefabric init' first.")


def init_workspace(home: Path) -> dict[str, object]:
    for name in ("operations", "idempotency", "artifacts", "approvals", "config"):
        (home / name).mkdir(parents=True, exist_ok=True)
    marker = home / "workspace.json"
    created = not marker.exists()
    if created:
        marker.write_text(
            json.dumps(
                {
                    "format": 1,
                    "mcp_profile": MCP_PROFILE,
                    "policy_bundle": "local-policy@1.0.0",
                },
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
    return {
        "workspace": str(home),
        "created": created,
        "initialized": True,
        "local_only": True,
    }


def parser() -> ServiceFabricArgumentParser:
    root = ServiceFabricArgumentParser(
        prog="servicefabric",
        description="A local developer command for reviewed ServiceFabric capabilities.",
        epilog="Start with: servicefabric init && servicefabric tools list",
    )
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("init", help="create or verify the local workspace")
    commands.add_parser("status", help="show the local environment")
    commands.add_parser("doctor", help="check local prerequisites")
    commands.add_parser("shell", help="open an interactive local shell")

    tools = commands.add_parser("tools", help="discover reviewed tools")
    tool_actions = tools.add_subparsers(dest="action", required=True)
    tool_actions.add_parser("list", help="list locally available tools")
    describe = tool_actions.add_parser("describe", help="describe one tool")
    describe.add_argument("tool_id")

    invoke = commands.add_parser("invoke", help="invoke a reviewed tool through governance")
    invoke.add_argument("tool_id")
    source = invoke.add_mutually_exclusive_group(required=True)
    source.add_argument("--arguments", metavar="JSON", help="tool arguments as JSON")
    source.add_argument("--arguments-file", metavar="PATH", help="file containing tool arguments")
    invoke.add_argument("--explain", action="store_true", help="show safe boundary decisions")

    apps = commands.add_parser("apps", help="inspect and build reviewed applications")
    app_actions = apps.add_subparsers(dest="action", required=True)
    app_actions.add_parser("list", help="list reviewed applications")
    app = app_actions.add_parser("describe", help="describe an application")
    app.add_argument("application_id")
    build = app_actions.add_parser("build", help="build an immutable local artifact")
    build.add_argument("application_id")
    build.add_argument("--revision", required=True)

    artifacts = commands.add_parser("artifacts", help="inspect immutable artifacts")
    artifact_actions = artifacts.add_subparsers(dest="action", required=True)
    artifact_actions.add_parser("list", help="list locally published artifacts")
    artifact = artifact_actions.add_parser("describe", help="describe an artifact")
    artifact.add_argument("digest")
    artifact = artifact_actions.add_parser("verify", help="verify artifact content")
    artifact.add_argument("digest")

    capsules = commands.add_parser("capsules", help="dispatch reviewed static capsules locally")
    capsule_actions = capsules.add_subparsers(dest="action", required=True)
    dispatch = capsule_actions.add_parser(
        "dispatch", help="open, dispatch, and close a local loopback capsule session"
    )
    dispatch.add_argument("--request-file", required=True, metavar="PATH")
    dispatch.add_argument("--method", default="GET", choices=("GET", "HEAD"))
    dispatch.add_argument("--path", default="/", help="declared capsule route")

    mcp = commands.add_parser("mcp", help="use the in-process MCP projection")
    mcp_actions = mcp.add_subparsers(dest="action", required=True)
    mcp_actions.add_parser("initialize", help="show local MCP capabilities")
    mcp_tools = mcp_actions.add_parser("tools", help="discover or call projected MCP tools")
    mcp_tool_actions = mcp_tools.add_subparsers(dest="mcp_action", required=True)
    mcp_tool_actions.add_parser("list", help="list projected MCP tools")
    mcp_call = mcp_tool_actions.add_parser("call", help="call a projected MCP tool")
    mcp_call.add_argument("tool_name")
    mcp_call.add_argument("--arguments", required=True, metavar="JSON")
    return root


def _extract_global_options(argv: list[str]) -> tuple[list[str], bool, bool, bool]:
    """Allow output flags before or after a subcommand without parser duplication."""
    json_mode = debug = verbose = False
    remaining: list[str] = []
    for item in argv:
        if item == "--json":
            json_mode = True
        elif item == "--debug":
            debug = True
        elif item == "--verbose":
            verbose = True
        else:
            remaining.append(item)
    return remaining, json_mode, debug, verbose


def _parse_arguments(raw: str) -> dict[str, object]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as error:
        raise ValueError("arguments must be valid JSON") from error
    if not isinstance(value, dict):
        raise ValueError("arguments must be a JSON object")
    return value


def dispatch(argv: list[str]) -> tuple[int, str, object]:
    selected, json_mode, _debug, verbose = _extract_global_options(argv)
    args = parser().parse_args(selected)
    home = workspace_path()
    if args.command == "init":
        return 0, "init", {**init_workspace(home), "json_mode": json_mode}
    if args.command == "shell":
        return 0, "shell", {"json_mode": json_mode}
    require_workspace(home)
    runtime = LocalRuntime(home)
    if args.command == "status":
        return 0, "status", {
            "workspace": str(home),
            "version": VERSION,
            "services": [
                "tool runtime",
                "governance",
                "durable operations",
                "application builder",
                "artifact store",
                "capsule host",
                "MCP projection (in-process)",
            ],
            "policy_bundle": "local-policy@1.0.0",
            "tools": 1,
            "applications": len(runtime.applications.list_applications()),
            "operations": len(list((home / "operations").glob("*"))),
            "mcp_profile": MCP_PROFILE,
            "limitations": "Local only. No public transport or production identity.",
            "json_mode": json_mode,
        }
    if args.command == "doctor":
        return 0, "doctor", {
            "checks": {
                "Python": sys.version.split()[0],
                "Workspace": "ready",
                "Policy bundle": "available",
                "Tool portfolio": "available",
                "Operation store": "readable",
                "Artifact store": "readable",
                "MCP profile": MCP_PROFILE,
            },
            "json_mode": json_mode,
        }
    if args.command == "tools":
        if args.action == "list":
            return 0, "tools-list", {
                "tools": [
                    {
                        "tool_id": "math.calculate",
                        "revision": "1.0.0",
                        "description": "Deterministic arithmetic calculation.",
                    }
                ],
                "json_mode": json_mode,
            }
        if args.tool_id != "math.calculate":
            raise ValueError(f"tool '{args.tool_id}' is not available locally")
        return 0, "tools-describe", {
            "tool_id": "math.calculate",
            "revision": "1.0.0",
            "description": "Deterministic arithmetic calculation.",
            "machine_callable": True,
            "effects": ["none"],
            "json_mode": json_mode,
        }
    if args.command == "invoke":
        if args.tool_id != "math.calculate":
            raise ValueError(f"tool '{args.tool_id}' is not available locally")
        raw = (
            Path(args.arguments_file).read_text(encoding="utf-8")
            if args.arguments_file
            else args.arguments
        )
        request, result = runtime.invoke_math(_parse_arguments(raw))
        value = {
            "request_id": request.spec.request_id,
            "revision": "1.0.0",
            "policy_outcome": "allow",
            "effective_authority": ["math-calculate"],
            "effective_budget": request.spec.budget.model_dump(mode="json"),
            "result": result,
            "json_mode": json_mode,
        }
        if args.explain or verbose:
            value["explain"] = [
                "Resolved reviewed tool revision 1.0.0.",
                "Constructed a canonical invocation request.",
                "Evaluated the local policy bundle.",
                "Applied effective authority and budget.",
                "Selected synchronous execution.",
                "Projected the canonical result.",
            ]
        return 0, "invoke", value
    if args.command == "apps":
        if args.action == "list":
            return 0, "apps-list", {
                "applications": list(runtime.applications.list_applications()),
                "json_mode": json_mode,
            }
        if args.action == "describe":
            return 0, "apps-describe", {
                "application": runtime.applications.describe_application(args.application_id),
                "json_mode": json_mode,
            }
        request_id = "local-build-{}-{}".format(
            args.application_id.replace(".", "-"), args.revision.replace(".", "-")
        )
        request = ApplicationBuildRequest.model_validate(
            {
                "apiVersion": "servicefabric.ai/v1alpha1",
                "kind": "ApplicationBuildRequest",
                "metadata": {
                    "id": request_id,
                    "name": "Local application build",
                    "description": "Bounded local developer application build.",
                    "owner_ref": {"kind": "service", "id": "servicefabric-cli"},
                },
                "spec": {
                    "request_id": request_id,
                    "application_id": args.application_id,
                    "revision": args.revision,
                    "caller_context": runtime.caller.model_dump(mode="json"),
                },
            }
        )
        return 0, "apps-build", {
            "build": runtime.applications.build_application(request),
            "json_mode": json_mode,
        }
    if args.command == "artifacts":
        if args.action == "list":
            return 0, "artifacts-list", {
                "artifacts": list(runtime.applications.list_artifacts()),
                "json_mode": json_mode,
            }
        if args.action == "describe":
            return 0, "artifacts-describe", {
                "artifact": runtime.artifacts.get_manifest(args.digest),
                "json_mode": json_mode,
            }
        return 0, "artifacts-verify", {
            "verification": runtime.artifacts.verify_artifact(args.digest),
            "json_mode": json_mode,
        }
    if args.command == "capsules":
        try:
            request = CapsuleHostRequest.model_validate_json(
                Path(args.request_file).read_text(encoding="utf-8")
            )
        except (OSError, ValueError) as error:
            raise ValueError("capsule request file is not a valid canonical request") from error
        session = runtime.capsules.open_session(request)
        try:
            response = runtime.capsules.dispatch(
                session, args.method, args.path, head_only=args.method == "HEAD"
            )
            return 0, "capsules-dispatch", {
                "capsule_id": request.spec.capsule_id,
                "revision": request.spec.capsule_revision,
                "status": response.status,
                "content_type": response.headers.get("Content-Type"),
                "body": response.body.decode("utf-8", errors="replace"),
                "json_mode": json_mode,
            }
        finally:
            runtime.capsules.close_session(session)
    if args.command == "mcp":
        now = datetime.now(timezone.utc)
        session_id = "local-mcp-session"
        context = TrustedMcpTransportContext(
            caller=runtime.caller, adapter_ref="trusted-mcp-adapter"
        )
        capabilities = McpClientCapabilities(structured_results=True)
        session, server = runtime.mcp.initialize(
            session_id=session_id,
            trusted_context=context,
            capabilities=capabilities,
            now=now,
        )
        if args.action == "initialize":
            return 0, "mcp-initialize", {
                "profile": MCP_PROFILE,
                "session": session,
                "capabilities": server,
                "transport": "in-process only",
                "json_mode": json_mode,
            }
        if args.mcp_action == "list":
            return 0, "mcp-tools-list", {
                "tools": runtime.mcp.list_tools(session_id=session_id, now=now).tools,
                "transport": "in-process only",
                "json_mode": json_mode,
            }
        call = McpCallRequest(
            request_id="local-mcp-call",
            tool_name=args.tool_name,
            correlation_id="local-mcp-correlation",
            arguments=_parse_arguments(args.arguments),
        )
        return 0, "mcp-tools-call", {
            "response": runtime.mcp.call(session_id=session_id, call=call, now=now),
            "transport": "in-process only",
            "json_mode": json_mode,
        }
    raise ValueError("unsupported command")


def human_output(command: str, value: object) -> str:
    data = as_json_value(value)
    assert isinstance(data, dict)
    if command == "init":
        action = "Created" if data["created"] else "Using"
        return f"{action} local workspace: {_display_workspace(Path(data['workspace']))}\nReady. Try: servicefabric tools list\n"
    if command == "status":
        return "\n".join(
            [
                "ServiceFabric local workspace",
                f"  Location: {_display_workspace(Path(data['workspace']))}",
                f"  Tools: {data['tools']}  Applications: {data['applications']}  Operations: {data['operations']}",
                f"  Policy: {data['policy_bundle']}",
                f"  MCP profile: {data['mcp_profile']}",
                f"  Note: {data['limitations']}",
                "",
            ]
        )
    if command == "doctor":
        checks = data["checks"]
        return "\n".join(["Local environment checks", *[f"  OK  {name}: {value}" for name, value in checks.items()], ""])
    if command == "tools-list":
        lines = ["Available tools"]
        lines.extend(f"  {tool['tool_id']:<24} {tool['description']}" for tool in data["tools"])
        return "\n".join([*lines, ""])
    if command == "tools-describe":
        return "\n".join(
            [
                data["tool_id"],
                f"  Revision: {data['revision']}",
                f"  {data['description']}",
                f"  Effects: {', '.join(data['effects'])}",
                "",
            ]
        )
    if command == "invoke":
        result = data["result"]
        if result["status"] == "success":
            answer = result.get("data", {}).get("value")
            lines = [f"{result['tool_id']} -> {answer}", f"  Revision: {data['revision']}  Policy: {data['policy_outcome']}"]
        else:
            error = result.get("error") or {}
            lines = [f"{result['tool_id']} failed: {error.get('message', 'unknown error')}"]
        if "explain" in data:
            lines.extend(["", "How this ran:", *[f"  - {item}" for item in data["explain"]]])
        return "\n".join([*lines, ""])
    if command == "apps-list":
        return "\n".join(["Reviewed applications", *[f"  {item}" for item in data["applications"]], ""])
    if command == "apps-describe":
        app = data["application"]
        return "\n".join([app["spec"]["display_name"], f"  ID: {app['spec']['application_id']}", f"  {app['spec']['description']}", ""])
    if command == "apps-build":
        build = data["build"]
        if build["status"] == "success":
            return f"Built {build['application_id']} {build['revision']}\n  Artifact: {build['artifact_digest']}\n"
        return f"Build failed: {build['errors'][0]['message']}\n"
    if command == "artifacts-describe":
        artifact = data["artifact"]
        return f"Artifact {artifact['spec']['artifact_digest']}\n  Files: {len(artifact['spec']['files'])}\n"
    if command == "artifacts-list":
        artifacts = data["artifacts"]
        if not artifacts:
            return "No local artifacts yet. Build an application first.\n"
        return "\n".join(["Local artifacts", *[f"  {digest}" for digest in artifacts], ""])
    if command == "artifacts-verify":
        verification = data["verification"]
        if verification["valid"]:
            return f"Artifact verified: {verification['artifact_digest']}\n  Files: {len(verification['verified_files'])}\n"
        return f"Artifact verification failed: {verification['artifact_digest']}\n"
    if command == "capsules-dispatch":
        if data["status"] == 200:
            return "\n".join(
                [
                    f"{data['capsule_id']} {data['revision']} -> {data['status']}",
                    f"  Content type: {data['content_type']}",
                    "  Session closed after local dispatch.",
                    "",
                ]
            )
        return f"Capsule route unavailable ({data['status']}).\n"
    if command == "mcp-initialize":
        capabilities = data["capabilities"]
        enabled = [name.replace("_", " ") for name, value in capabilities.items() if value]
        return "\n".join(
            [
                f"MCP projection ready ({data['profile']})",
                f"  Capabilities: {', '.join(enabled)}",
                "  Transport: in-process only",
                "",
            ]
        )
    if command == "mcp-tools-list":
        tools = data["tools"]
        return "\n".join(
            ["Projected MCP tools", *[f"  {tool['name']:<24} {tool['description']}" for tool in tools], ""]
        )
    if command == "mcp-tools-call":
        response = data["response"]
        if response["error"] is not None:
            return f"MCP call failed: {response['error']['message']}\n"
        result = response["structured_content"]
        if isinstance(result, dict) and "value" in result:
            return f"MCP {response['request_id']} -> {result['value']}\n"
        return "MCP call completed. Use --json for the structured result.\n"
    return json_output(data)


def emit(command: str, value: object) -> None:
    data = as_json_value(value)
    if isinstance(data, dict) and data.pop("json_mode", False):
        print(json_output(data), end="")
    else:
        print(human_output(command, data), end="")


def run_shell() -> int:
    print("ServiceFabric local developer shell")
    print(f"workspace: {_display_workspace(workspace_path())}")
    print("Type 'help' for examples or 'exit' to leave.")
    while True:
        try:
            line = input("sf> ").strip()
        except EOFError:
            print()
            return 0
        if line in {"exit", "quit"}:
            return 0
        if line == "help":
            print("Try: tools list | invoke math.calculate --arguments '{\"expression\": \"12 / 3\"}' | status")
            continue
        if not line:
            continue
        try:
            code, command, value = dispatch(shlex.split(line))
            emit(command, value)
            if code:
                return code
        except (CliUsageError, ValueError) as error:
            print(f"error: {error}")


def main(argv: list[str] | None = None) -> int:
    selected = sys.argv[1:] if argv is None else argv
    if selected == ["shell"]:
        return run_shell()
    try:
        code, command, value = dispatch(selected)
        emit(command, value)
        return code
    except CliUsageError as error:
        print(f"error: {error}. Run 'servicefabric --help' for usage.", file=sys.stderr)
        return 2
    except Exception as error:
        _remaining, _json_mode, debug, _verbose = _extract_global_options(selected)
        if debug:
            raise
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
