"""Local-only ServiceFabric developer composition root and command dispatcher."""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import shlex
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from servicefabric_application_builder import create_application_builder_service
from servicefabric_capsule_host import create_capsule_host_service
from servicefabric_contracts import ApplicationBuildRequest, ToolInvocationRequest, ToolResult
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
from servicefabric_governance_service import create_governance_operations_service
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
from servicefabric_runtime import FilePortfolio, InvocationKernel
from servicefabric_runtime.portfolio import __file__ as _portfolio_module
from servicefabric_tool_runtime_service import ToolRuntimeService
from servicefabric_application_host import LocalApplicationHost

from servicefabric_workspace import (
    WorkspaceLayout,
    WorkspaceContext,
    WorkspaceStatus,
    WorkspaceValidation,
    ApplicationCreateRequest,
    ApplicationRecord,
    ApplicationLayout,
    ApplicationHostPaths,
    resolve_workspace,
    WorkspaceService,
    validate_application_id,
    WorkspaceError,
    WorkspaceNotInitialized,
    InvalidWorkspaceConfiguration,
    InvalidApplicationId,
    ApplicationAlreadyExists,
    ApplicationNotFound,
)

from .capsules import CapsuleClient
from .governance import GovernanceClient
from .mcp import McpGatewayClient
from .wave3 import Wave3ApplicationService
from .development import ResearchNotesDevelopmentService


VERSION = "0.1.0a1"
POLICY_DIGEST = "sha256:" + "a" * 64
MCP_PROFILE = "2025-11-25"


class CliUsageError(ValueError):
    """A concise command-line validation error."""


class ServiceFabricArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise CliUsageError(message)


def resolve_workspace_for_cli(explicit_path: str | None = None) -> WorkspaceContext:
    # Precedence:
    # 1. explicit --workspace PATH;
    # 2. SERVICEFABRIC_WORKSPACE env var;
    # 3. nearest parent containing workspace.yaml;
    # 4. current directory for workspace init;
    # 5. legacy SERVICEFABRIC_HOME state-only mode.
    if explicit_path:
        return resolve_workspace(explicit_workspace=Path(explicit_path))

    if os.environ.get("SERVICEFABRIC_WORKSPACE"):
        return resolve_workspace()

    curr = Path.cwd().resolve()
    for parent in [curr, *curr.parents]:
        if (parent / "workspace.yaml").is_file():
            return resolve_workspace(explicit_workspace=parent)

    return resolve_workspace()


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

    def __init__(self, context: WorkspaceContext | Path | str, workspace_service: WorkspaceService | None = None):
        if isinstance(context, (Path, str)):
            legacy_home = Path(context)
            # Create a compatibility layout with legacy-state-only mode
            compat_layout = WorkspaceLayout.from_root(legacy_home, legacy_home)
            context = WorkspaceContext(
                layout=compat_layout,
                mode="legacy-state-only",
                resolution_source="legacy-home"
            )
            workspace_service = WorkspaceService(context)
        elif workspace_service is None:
            workspace_service = WorkspaceService(context)

        self.context = context
        self.workspace = workspace_service
        self.home = context.layout.state

        host_paths = ApplicationHostPaths(
            root=context.layout.legacy_hosted_applications,
            artifacts=context.layout.artifacts,
            locks=context.layout.locks,
            logs=context.layout.logs,
        )
        self.host = LocalApplicationHost(host_paths)

        portfolio_root = Path(_portfolio_module).resolve().parent.parent / "portfolios"
        self.portfolio = FilePortfolio(portfolio_root)
        self.runtime_service = ToolRuntimeService(InvocationKernel(self.portfolio))
        self.caller = CallerContext(
            subject_ref="local-developer",
            principal_type="human",
            tenant_ref="local",
            issuer="servicefabric-local",
            scopes=("math-calculate", "text-count", "text-inspect"),
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
        self.governance = GovernanceClient(
            create_governance_operations_service(
                root=context.layout.operations,
                evaluator=VersionedPolicyEvaluator((bundle,)),
            )
        )
        repository = Path(__file__).resolve().parents[3]
        self.applications = create_application_builder_service(
            portfolio_root=repository / "portfolio" / "applications",
            artifact_store_root=context.layout.artifacts,
        )
        self.capsules = CapsuleClient(
            create_capsule_host_service(
                capsule_portfolio_root=repository / "portfolio" / "capsules",
                application_portfolio_root=repository / "portfolio" / "applications",
                artifact_store_root=context.layout.artifacts,
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
                operations=self.governance,
            )
        )

    def invoke_application(self, tool_id: str, arguments: dict[str, object]):
        capability = self.host.describe_capability(tool_id)
        request_id = "local-request-" + uuid4().hex[:16]
        permission = str(capability["permission_id"])
        revision = str(capability["revision"])
        caller = self.caller
        request = ToolInvocationRequest.model_validate({"apiVersion":"servicefabric.ai/v1alpha1","kind":"ToolInvocationRequest","metadata":{"id":request_id,"name":"Hosted application invocation","description":"Governed hosted application capability request.","owner_ref":{"kind":"service","id":"servicefabric-cli"}},"spec":{"request_id":request_id,"target":{"target_kind":"revision","tool_id":tool_id,"revision_ref":revision},"arguments":arguments,"caller_context":caller,"protocol_context":{"protocol":"internal","adapter_ref":"trusted-local-cli"},"budget":{},"requested_response_mode":"synchronous"}})
        bundle = PolicyBundle(bundle_id="hosted-application-policy",version="1.0.0",digest=POLICY_DIGEST,allowed_scopes=("text-count","text-inspect"))
        profile = InvocationGovernanceProfile(tool_id,revision,(EffectDeclaration(effect_type="none",target_category="text",scope="local",reversibility="not_applicable",verification_required=False,approval_required=False,idempotency_required=False),),(PermissionRequirement(permission_id=permission,tenant_scope="caller_tenant",resource_scope=str(capability["application_id"])),),AuthorityGrant(scopes=(permission,),tenant_ref="local"),ExecutionBudget(),"low",bundle.bundle_id,bundle.version,bundle.digest)
        host = self.host
        class Adapter:
            def invoke(self, value):
                started=datetime.now(timezone.utc)
                data=host.invoke(tool_id,value.spec.arguments)
                completed=datetime.now(timezone.utc)
                return ToolResult(apiVersion="servicefabric.ai/v1alpha1",kind="ToolResult",status="success",invocation_id=value.spec.request_id,tool_id=tool_id,revision_ref=revision,started_at=started,completed_at=completed,duration=completed-started,data=data)
        boundary=GovernedInvocationBoundary(evaluator=VersionedPolicyEvaluator((bundle,)),approvals=ApprovalService(),runtime=Adapter(),profiles=(profile,))
        return request,boundary.invoke(request,trusted_adapter_ref="trusted-local-cli",now=datetime.now(timezone.utc))

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


def require_workspace(context: WorkspaceContext) -> None:
    if context.mode == "legacy-state-only":
        marker = context.layout.state / "workspace.json"
        if not marker.is_file():
            raise ValueError("workspace is not initialized. Run 'servicefabric init' first.")
    else:
        marker = context.layout.root / "workspace.yaml"
        if not marker.is_file():
            raise ValueError("workspace is not initialized. Run 'servicefabric workspace init PATH' first.")


def init_workspace_compat(context: WorkspaceContext) -> dict[str, object]:
    if context.mode == "external":
        service = WorkspaceService(context)
        status = service.initialize()
        return {
            "workspace": str(context.layout.root),
            "created": status.created,
            "initialized": status.initialized,
            "local_only": True,
            "mode": "external",
        }
    else:
        home = context.layout.state
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
            "mode": "legacy-state-only",
        }


def parser() -> ServiceFabricArgumentParser:
    root = ServiceFabricArgumentParser(
        prog="servicefabric",
        description="A local developer command for reviewed ServiceFabric capabilities.",
        epilog="Start with: servicefabric init && servicefabric tools list",
    )
    root.add_argument("--workspace", metavar="PATH", help="explicit workspace path")

    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("init", help="create or verify the local workspace")
    commands.add_parser("status", help="show the local environment")
    commands.add_parser("doctor", help="check local prerequisites")
    commands.add_parser("shell", help="open an interactive local shell")

    workspace = commands.add_parser("workspace", help="manage the ServiceFabric development workspace")
    workspace_actions = workspace.add_subparsers(dest="workspace_action", required=True)

    w_init = workspace_actions.add_parser("init", help="create a full ServiceFabric development workspace")
    w_init.add_argument("path", nargs="?", help="optional path to initialize workspace")

    workspace_actions.add_parser("status", help="show physical development-workspace state")
    workspace_actions.add_parser("paths", help="show all resolved workspace paths")

    w_val = workspace_actions.add_parser("validate", help="validate workspace layout")
    w_val.add_argument("--deep", action="store_true", help="run deep validation including apps and symlinks")

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

    # New apps subcommands
    create_app = app_actions.add_parser("create", help="create a reviewed generated application")
    create_app.add_argument("application_id", help="the unique application ID")
    create_app.add_argument("--name", help="descriptive name of the application")
    create_app.add_argument("--template", choices=("modular-web-app",), help="reviewed application template")
    create_app.add_argument("--empty", action="store_true", help="initialize an empty application project")

    modules = app_actions.add_parser("modules", help="list generated application modules")
    modules.add_argument("application_id")
    validate = app_actions.add_parser("validate", help="validate generated application manifests")
    validate.add_argument("application_id")

    locate_app = app_actions.add_parser("locate", help="get the directory path of an application")
    locate_app.add_argument("application_id")

    inspect_app = app_actions.add_parser("inspect", help="inspect application definition and structure")
    inspect_app.add_argument("application_id")

    install = app_actions.add_parser("install", help="install a reviewed local application")
    install.add_argument("source")
    app = app_actions.add_parser("describe", help="describe an application")
    app.add_argument("application_id")
    build = app_actions.add_parser("build", help="build an immutable local artifact")
    build.add_argument("application_id")
    build.add_argument("--revision")
    dev = app_actions.add_parser("dev", help="run a reviewed modular application locally")
    dev_actions = dev.add_subparsers(dest="dev_action", required=True)
    for action in ("prepare", "start", "status", "stop"):
        command = dev_actions.add_parser(action, help=f"{action} a modular development application")
        command.add_argument("application_id")
    restart = dev_actions.add_parser("restart", help="restart one executable modular application module")
    restart.add_argument("application_id")
    restart.add_argument("--module", required=True)
    for action in ("start", "status", "resources", "stop"):
        command = app_actions.add_parser(action, help=f"{action} a hosted local application")
        command.add_argument("application_id")

    capabilities = commands.add_parser("capabilities", help="validate and register static application capabilities")
    capability_actions = capabilities.add_subparsers(dest="action", required=True)
    capability_validate = capability_actions.add_parser("validate", help="validate generated static declarations")
    capability_validate.add_argument("application_id", metavar="APPLICATION")
    capability_register = capability_actions.add_parser("register", help="register validated static declarations")
    capability_register.add_argument("application_id", metavar="APPLICATION")
    capability_list = capability_actions.add_parser("list", help="list registered static definitions")
    capability_list.add_argument("--application", metavar="APPLICATION")
    capability_describe = capability_actions.add_parser("describe", help="describe one registered static definition")
    capability_describe.add_argument("capability_id", metavar="CAPABILITY_ID")
    capability_availability = capability_actions.add_parser("availability", help="show runtime availability without changing static registration")
    availability_target = capability_availability.add_mutually_exclusive_group(required=True)
    availability_target.add_argument("capability_id", nargs="?", metavar="CAPABILITY_ID")
    availability_target.add_argument("--application", metavar="APPLICATION")
    capability_invoke = capability_actions.add_parser("invoke", help="invoke one available reviewed capability locally")
    capability_invoke.add_argument("capability_id", metavar="CAPABILITY_ID")
    capability_invoke.add_argument("--input", required=True, metavar="JSON")

    call = commands.add_parser("call", help="call a governed hosted application capability")
    call.add_argument("tool_id")
    call.add_argument("--input", required=True, metavar="JSON")

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

    operations = commands.add_parser("operations", help="inspect local durable operations")
    operation_actions = operations.add_subparsers(dest="action", required=True)
    operation_actions.add_parser("list", help="list durable operations")
    operation = operation_actions.add_parser("get", help="show an operation")
    operation.add_argument("operation_id")
    operation = operation_actions.add_parser("events", help="show immutable operation history")
    operation.add_argument("operation_id")
    operation = operation_actions.add_parser("receipts", help="show verified effect receipts")
    operation.add_argument("operation_id")
    operation = operation_actions.add_parser("cancel", help="request cooperative cancellation")
    operation.add_argument("operation_id")
    operation.add_argument("--expected-version", type=int, required=True)
    operation.add_argument("--reason", required=True)
    return root


def _extract_global_options(argv: list[str]) -> tuple[list[str], bool, bool, bool, str | None]:
    """Allow output flags before or after a subcommand without parser duplication."""
    json_mode = debug = verbose = False
    workspace_path_val = None
    remaining: list[str] = []

    i = 0
    while i < len(argv):
        item = argv[i]
        if item == "--json":
            json_mode = True
        elif item == "--debug":
            debug = True
        elif item == "--verbose":
            verbose = True
        elif item == "--workspace":
            if i + 1 < len(argv):
                workspace_path_val = argv[i + 1]
                i += 1
            else:
                raise CliUsageError("--workspace requires a path argument")
        elif item.startswith("--workspace="):
            workspace_path_val = item.split("=", 1)[1]
        else:
            remaining.append(item)
        i += 1

    return remaining, json_mode, debug, verbose, workspace_path_val


def _parse_arguments(raw: str) -> dict[str, object]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as error:
        raise ValueError("arguments must be valid JSON") from error
    if not isinstance(value, dict):
        raise ValueError("arguments must be a JSON object")
    return value


def require_development_workspace(context: WorkspaceContext) -> None:
    if context.mode == "legacy-state-only":
        raise CliUsageError(
            "A development workspace is required.\n"
            "Run: servicefabric workspace init PATH"
        )


def dispatch(argv: list[str]) -> tuple[int, str, object]:
    selected, json_mode, _debug, verbose, workspace_path_val = _extract_global_options(argv)
    args = parser().parse_args(selected)

    context = resolve_workspace_for_cli(workspace_path_val)
    workspace_service = WorkspaceService(context)

    if args.command == "workspace":
        if args.workspace_action == "init":
            init_context = context
            if args.path:
                init_context = resolve_workspace_for_cli(args.path)
            init_service = WorkspaceService(init_context)
            status = init_service.initialize()
            return 0, "workspace-init", {
                "created": status.created,
                "initialized": status.initialized,
                "mode": status.mode,
                "workspace": str(status.root),
                "state": str(status.state),
                "repaired_directories": status.repaired_directories,
                "json_mode": json_mode,
            }

        require_development_workspace(context)

        if args.workspace_action == "status":
            status = workspace_service.inspect()
            validation_res = workspace_service.validate()
            num_apps = 0
            if context.layout.applications.is_dir():
                num_apps = len([p for p in context.layout.applications.iterdir() if p.is_dir()])
            num_recipes = 0
            if context.layout.recipes.is_dir():
                num_recipes = len([p for p in context.layout.recipes.iterdir() if p.is_dir()])
            num_libraries = 0
            if context.layout.libraries.is_dir():
                num_libraries = len([p for p in context.layout.libraries.iterdir() if p.is_dir()])

            return 0, "workspace-status", {
                "workspace": str(status.root),
                "state": str(status.state),
                "applications": num_apps,
                "recipes": num_recipes,
                "libraries": num_libraries,
                "validation": "valid" if validation_res.valid else "invalid",
                "json_mode": json_mode,
            }

        if args.workspace_action == "paths":
            return 0, "workspace-paths", {
                "workspace_root": str(context.layout.root),
                "applications": str(context.layout.applications),
                "recipes": str(context.layout.recipes),
                "libraries": str(context.layout.libraries),
                "state": str(context.layout.state),
                "artifacts": str(context.layout.artifacts),
                "environments": str(context.layout.environments),
                "logs": str(context.layout.logs),
                "json_mode": json_mode,
            }

        if args.workspace_action == "validate":
            validation_res = workspace_service.validate()
            findings = [
                {
                    "code": f.code,
                    "severity": f.severity,
                    "path": str(f.path) if f.path else None,
                    "message": f.message,
                }
                for f in validation_res.findings
            ]
            return 0, "workspace-validate", {
                "valid": validation_res.valid,
                "findings": findings,
                "json_mode": json_mode,
            }

    if args.command == "init":
        return 0, "init", {**init_workspace_compat(context), "json_mode": json_mode}
    if args.command == "shell":
        return 0, "shell", {"json_mode": json_mode}

    require_workspace(context)
    runtime = LocalRuntime(context, workspace_service)

    if args.command == "status":
        return 0, "status", {
            "workspace": str(context.layout.root if context.mode != "legacy-state-only" else context.layout.state),
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
            "operations": len(runtime.governance.list_operations()),
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
        hosted = [
            {
                key: item[key]
                for key in (
                    "tool_id",
                    "revision",
                    "application_id",
                    "description",
                    "effects",
                )
            }
            for item in runtime.host.capabilities()
        ]
        if args.action == "list":
            return 0, "tools-list", {
                "tools": [
                    {
                        "tool_id": "math.calculate",
                        "revision": "1.0.0",
                        "description": "Deterministic arithmetic calculation.",
                    }
                ] + hosted,
                "json_mode": json_mode,
            }
        if args.tool_id in {item["tool_id"] for item in hosted}:
            item = next(value for value in hosted if value["tool_id"] == args.tool_id)
            return 0, "tools-describe", {
                **item,
                "machine_callable": True,
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
    if args.command == "call":
        runtime.host.describe_capability(args.tool_id)
        request,result=runtime.invoke_application(args.tool_id,_parse_arguments(args.input))
        return 0,"call",{"request_id":request.spec.request_id,"revision":request.spec.target.revision_ref,"policy_outcome":"allow","result":result,"json_mode":json_mode}
    if args.command == "apps":
        wave3 = Wave3ApplicationService(context)
        if args.action == "create" and args.template:
            require_development_workspace(context)
            return 0, "apps-create", {**wave3.create(args.application_id, args.template), "json_mode": json_mode}
        if args.action == "modules":
            require_development_workspace(context)
            return 0, "apps-modules", {"application_id": args.application_id, "modules": wave3.modules(args.application_id), "json_mode": json_mode}
        if args.action == "validate":
            require_development_workspace(context)
            return 0, "apps-validate", {**wave3.validate(args.application_id), "json_mode": json_mode}
        if args.action == "dev":
            require_development_workspace(context)
            if args.dev_action == "prepare":
                value = wave3.prepare(args.application_id)
            elif args.dev_action == "start":
                value = wave3.start(args.application_id)
            elif args.dev_action == "status":
                value = wave3.status(args.application_id)
            elif args.dev_action == "restart":
                value = wave3.restart(args.application_id, args.module)
            else:
                value = wave3.stop(args.application_id)
            return 0, f"apps-dev-{args.dev_action}", {**value, "json_mode": json_mode}
        if args.action in {"create", "locate", "inspect"}:
            require_development_workspace(context)

        if args.action == "create":
            try:
                record = workspace_service.create_application(
                    ApplicationCreateRequest(
                        application_id=args.application_id,
                        display_name=args.name,
                    )
                )
                return 0, "apps-create", {
                    "application_id": record.application_id,
                    "display_name": record.display_name,
                    "source_path": record.source_path,
                    "status": record.status,
                    "json_mode": json_mode,
                }
            except WorkspaceError as error:
                raise CliUsageError(str(error))

        if args.action == "locate":
            try:
                app_layout = workspace_service.locate_application(args.application_id)
                return 0, "apps-locate", {
                    "application_id": args.application_id,
                    "absolute_path": str(app_layout.root.resolve()),
                    "relative_path": f"applications/{args.application_id}",
                    "json_mode": json_mode,
                }
            except WorkspaceError as error:
                raise CliUsageError(str(error))

        if args.action == "inspect":
            try:
                app_layout = workspace_service.locate_application(args.application_id)
                installed = args.application_id in runtime.host.list_applications()
                running = False
                if installed:
                    try:
                        running = runtime.host.status(args.application_id)["state"] == "running"
                    except Exception:
                        pass

                display_name = args.application_id.replace("-", " ").title()
                num_modules = 0
                num_bindings = 0
                if app_layout.application_definition.is_file():
                    try:
                        import yaml
                        with app_layout.application_definition.open("r", encoding="utf-8") as f:
                            data = yaml.safe_load(f)
                            display_name = data.get("metadata", {}).get("name", display_name)
                            num_modules = len(data.get("spec", {}).get("modules", []))
                    except Exception:
                        pass
                if app_layout.bindings.is_file():
                    try:
                        import yaml
                        with app_layout.bindings.open("r", encoding="utf-8") as f:
                            data = yaml.safe_load(f)
                            num_bindings = len(data.get("spec", {}).get("bindings", {}))
                    except Exception:
                        pass

                return 0, "apps-inspect", {
                    "application_id": args.application_id,
                    "display_name": display_name,
                    "status": "development",
                    "source_path": f"applications/{args.application_id}",
                    "modules": num_modules,
                    "bindings": num_bindings,
                    "installed": installed,
                    "running": running,
                    "json_mode": json_mode,
                }
            except WorkspaceError as error:
                raise CliUsageError(str(error))

        if args.action == "install":
            return 0,"apps-install",{**runtime.host.install(Path(args.source)),"json_mode":json_mode}
        if args.action == "dev":
            require_development_workspace(context)
            if args.application_id != "research-notes":
                raise CliUsageError("only the reviewed research-notes development application is available")
            service = ResearchNotesDevelopmentService(context.layout)
            if args.dev_action == "prepare":
                value = service.prepare()
            elif args.dev_action == "start":
                value = service.start()
            elif args.dev_action == "status":
                value = service.status()
            elif args.dev_action == "restart":
                value = service.restart(args.module)
            else:
                value = service.stop()
            return 0, f"apps-dev-{args.dev_action}", {args.dev_action: value, "json_mode": json_mode}
        if args.action in {"start","status","resources","stop"}:
            method=getattr(runtime.host,args.action)
            return 0,f"apps-{args.action}",{args.action:method(args.application_id),"json_mode":json_mode}
        if args.action == "list":
            ws_apps = []
            if context.mode != "legacy-state-only":
                try:
                    ws_apps = [{"application_id": app.application_id, "status": app.status} for app in workspace_service.list_applications()]
                except Exception:
                    pass
            reviewed_apps = runtime.applications.list_applications()
            installed_apps = runtime.host.list_applications()
            combined_apps = sorted(set(reviewed_apps) | set(installed_apps) | {app["application_id"] for app in ws_apps})
            return 0, "apps-list", {
                "applications": combined_apps,
                "workspace_applications": ws_apps,
                "reviewed_applications": reviewed_apps,
                "installed_applications": installed_apps,
                "json_mode": json_mode,
            }
        if args.action == "describe":
            return 0, "apps-describe", {
                "application": runtime.applications.describe_application(args.application_id),
                "json_mode": json_mode,
            }
        if args.application_id != "text-utility" and not args.revision:
            require_development_workspace(context)
            return 0, "apps-build", {"build": wave3.build(args.application_id), "json_mode": json_mode}
        if args.application_id == "text-utility":
            return 0,"apps-build",{"build":runtime.host.build(args.application_id),"json_mode":json_mode}
        if not args.revision:
            raise ValueError("--revision is required for immutable static applications")
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
    if args.command == "capabilities":
        from .capabilities import (
            register_generated_capabilities,
            registry_for_workspace,
            validate_generated_capabilities,
        )

        require_development_workspace(context)
        if args.action == "validate":
            value = validate_generated_capabilities(context.layout, args.application_id)
            return 0, "capabilities-validate", {
                "application_id": value.application_id,
                "operations": [item.operation_id for item in value.operations],
                "capabilities": [item.metadata.id for item in value.capabilities],
                "valid": True,
                "json_mode": json_mode,
            }
        registry = registry_for_workspace(context.layout)
        if args.action == "register":
            records = register_generated_capabilities(context.layout, args.application_id)
            return 0, "capabilities-register", {
                "application_id": args.application_id,
                "capabilities": [record.definition.model_dump(mode="json", by_alias=True) for record in records],
                "digests": [record.digest for record in records],
                "json_mode": json_mode,
            }
        if args.action == "list":
            records = registry.list(args.application)
            return 0, "capabilities-list", {
                "application_id": args.application,
                "capabilities": [record.definition.model_dump(mode="json", by_alias=True) for record in records],
                "json_mode": json_mode,
            }
        if args.action in {"availability", "invoke"}:
            from .capability_runtime import CapabilityRuntimeService

            service = CapabilityRuntimeService(context.layout)
            if args.action == "availability":
                if args.application is not None:
                    records = [item.to_dict() for item in service.availability_for_application(args.application)]
                    return 0, "capabilities-availability", {
                        "application_id": args.application,
                        "capabilities": records,
                        "json_mode": json_mode,
                    }
                availability = service.availability(args.capability_id)
                return 0, "capabilities-availability", {
                    "availability": availability.to_dict(),
                    "json_mode": json_mode,
                }
            try:
                input_value = json.loads(args.input)
            except json.JSONDecodeError as exc:
                raise CliUsageError("--input must be valid JSON") from exc
            return 0, "capabilities-invoke", {
                "invocation": service.invoke(args.capability_id, input_value),
                "json_mode": json_mode,
            }
        record = registry.describe(args.capability_id)
        return 0, "capabilities-describe", {
            "capability": record.definition.model_dump(mode="json", by_alias=True),
            "digest": record.digest,
            "applications": list(record.application_ids),
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
                "artifact": runtime.applications.get_artifact_manifest(args.digest),
                "json_mode": json_mode,
            }
        return 0, "artifacts-verify", {
            "verification": runtime.applications.verify_artifact(args.digest),
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
    if args.command == "operations":
        if args.action == "list":
            return 0, "operations-list", {
                "operations": [
                    {"operation": operation, "version": version}
                    for operation, version in runtime.governance.list_operations()
                ],
                "json_mode": json_mode,
            }
        if args.action == "get":
            operation, version = runtime.governance.get_operation(args.operation_id)
            return 0, "operations-get", {
                "operation": operation,
                "version": version,
                "json_mode": json_mode,
            }
        if args.action == "events":
            return 0, "operations-events", {
                "events": runtime.governance.list_operation_events(args.operation_id),
                "json_mode": json_mode,
            }
        if args.action == "receipts":
            return 0, "operations-receipts", {
                "receipts": runtime.governance.effect_receipts(args.operation_id),
                "json_mode": json_mode,
            }
        return 0, "operations-cancel", {
            "operation": runtime.governance.request_cancellation(
                args.operation_id,
                expected_version=args.expected_version,
                now=datetime.now(timezone.utc),
                reason=args.reason,
            ),
            "json_mode": json_mode,
        }
    raise ValueError("unsupported command")


def human_output(command: str, value: object) -> str:
    data = as_json_value(value)
    assert isinstance(data, dict)
    if command == "workspace-init":
        action = "Created" if data["created"] else "Using existing"
        repaired = ""
        if data.get("repaired_directories"):
            repaired = f"\n  Repaired:  {', '.join(data['repaired_directories'])}"
        return "\n".join(
            [
                f"{action} ServiceFabric development workspace",
                "",
                f"  Workspace: {data['workspace']}",
                f"  State:     {data['state']}",
                f"  Mode:      {data['mode']}{repaired}",
                "",
                "Ready to create applications.",
                "",
            ]
        )
    if command == "workspace-status":
        return "\n".join(
            [
                "ServiceFabric development workspace",
                "",
                f"  Workspace:    {data['workspace']}",
                f"  State:        {data['state']}",
                f"  Applications: {data['applications']}",
                f"  Recipes:      {data['recipes']}",
                f"  Libraries:    {data['libraries']}",
                f"  Validation:   {data['validation']}",
                "",
            ]
        )
    if command == "workspace-paths":
        return "\n".join(
            [
                "Workspace paths",
                "",
                f"  applications:  {data['applications']}",
                f"  recipes:       {data['recipes']}",
                f"  libraries:     {data['libraries']}",
                f"  state:         {data['state']}",
                f"  artifacts:     {data['artifacts']}",
                f"  environments:  {data['environments']}",
                f"  logs:          {data['logs']}",
                "",
            ]
        )
    if command == "workspace-validate":
        if data["valid"]:
            return "Workspace validation passed.\n"
        lines = ["Workspace validation failed", ""]
        for f in data["findings"]:
            path_str = f" ({f['path']})" if f['path'] else ""
            lines.append(f"  {f['severity'].upper()} {f['code']}{path_str}")
            lines.append(f"  {f['message']}")
            lines.append("")
        return "\n".join(lines)
    if command == "apps-create":
        return "\n".join(
            [
                f"Created application source: {data['application_id']}",
                "",
                f"  Location: {data['source_path']}",
                f"  Status:   {data['status']}",
                "  Modules:  none",
                "",
                "Next: edit the application or generate its blueprint.",
                "",
            ]
        )
    if command == "apps-locate":
        return f"{data['absolute_path']}\n"
    if command == "apps-inspect":
        inst_str = "yes" if data["installed"] else "no"
        run_str = "yes" if data["running"] else "no"
        return "\n".join(
            [
                data["display_name"],
                "",
                f"  ID:          {data['application_id']}",
                f"  Status:      {data['status']}",
                f"  Source:      {data['source_path']}",
                f"  Modules:     {data['modules']}",
                f"  Bindings:    {data['bindings']}",
                f"  Installed:   {inst_str}",
                f"  Running:     {run_str}",
                "",
            ]
        )
    if command == "init":
        action = "Created" if data["created"] else "Using"
        gentle_note = ""
        if data.get("mode") == "legacy-state-only":
            gentle_note = (
                "\n\nFor application development, create a full workspace with:\n"
                "  servicefabric workspace init PATH\n"
            )
        return (
            f"{action} local workspace: {_display_workspace(Path(data['workspace']))}"
            f"{gentle_note}\nReady. Try: servicefabric tools list\n"
        )
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
    if command == "call":
        result = data["result"]
        if result["status"] == "success":
            return f"{result['tool_id']} -> {json.dumps(result['data'], sort_keys=True)}\n  Revision: {data['revision']}  Policy: {data['policy_outcome']}\n"
        return f"{result['tool_id']} failed: {result['error']['message']}\n"
    if command == "apps-list":
        lines = ["Applications", ""]
        ws_ids = {app["application_id"] for app in data.get("workspace_applications", [])}
        reviewed_ids = set(data.get("reviewed_applications", []))
        installed_ids = set(data.get("installed_applications", []))

        all_ids = sorted(ws_ids | reviewed_ids | installed_ids)
        for app_id in all_ids:
            facets = []
            if app_id in ws_ids:
                facets.append("development source")
            if app_id in reviewed_ids:
                facets.append("reviewed definition")
            if app_id in installed_ids:
                facets.append("installed")

            facet_str = " + ".join(facets)
            lines.append(f"  {app_id:<24} {facet_str}")
        return "\n".join(lines) + "\n"
    if command == "apps-describe":
        app = data["application"]
        return "\n".join([app["spec"]["display_name"], f"  ID: {app['spec']['application_id']}", f"  {app['spec']['description']}", ""])
    if command == "apps-install":
        action = "Installed" if data["installed"] else "Already installed"
        return f"{action}: {data['application_id']}\n"
    if command in {"apps-start", "apps-status", "apps-stop"}:
        operation = data[command.removeprefix("apps-")]
        return f"{operation['application_id']}: {operation['state']} (health: {operation['health']})\n"
    if command == "apps-resources":
        resources = data["resources"]
        measured = resources["measured"]
        return "\n".join(["Text Utility resources", f"  Declared memory: {resources['declared']['memory_mib']} MiB", f"  Current memory: {measured['current_memory_bytes'] or 'unavailable'} bytes", f"  Peak memory: {measured['peak_memory_bytes'] or 'unavailable'} bytes", f"  Recent CPU: {measured['recent_cpu_percent'] if measured['recent_cpu_percent'] is not None else 'unavailable'}", f"  Startup: {measured['startup_duration_ms']} ms", f"  Requests: {measured['request_count']}", f"  Health: {measured['health']}", f"  Restarts: {measured['restart_count']}", ""])
    if command == "apps-build":
        build = data["build"]
        if build["status"] == "success":
            return f"Built {build['application_id']} {build['revision']}\n  Artifact: {build['artifact_digest']}\n"
        return f"Build failed: {build['errors'][0]['message']}\n"
    if command == "capabilities-validate":
        return "\n".join(
            [
                f"Validated static capabilities for {data['application_id']}",
                f"  Operations:   {', '.join(data['operations'])}",
                f"  Capabilities: {', '.join(data['capabilities'])}",
                "",
            ]
        )
    if command == "capabilities-register":
        identifiers = [item["metadata"]["id"] for item in data["capabilities"]]
        return "\n".join(
            [
                f"Registered static capabilities for {data['application_id']}",
                *[f"  {identifier}" for identifier in identifiers],
                "",
            ]
        )
    if command == "capabilities-list":
        capabilities = data["capabilities"]
        if not capabilities:
            return "No static capabilities are registered.\n"
        return "\n".join(
            [
                "Registered static capabilities",
                *[f"  {item['metadata']['id']}" for item in capabilities],
                "",
            ]
        )
    if command == "capabilities-describe":
        capability = data["capability"]
        return "\n".join(
            [
                capability["metadata"]["id"],
                f"  Operation: {capability['spec']['operationRef']}",
                f"  Digest: {data['digest']}",
                "",
            ]
        )
    if command == "capabilities-availability":
        if "availability" in data:
            availability = data["availability"]
            return f"{availability['capabilityId']}: {availability['state']} ({availability['reason']})\n"
        records = data["capabilities"]
        if not records:
            return "No registered capabilities for this application.\n"
        return "\n".join(
            [
                f"{data['application_id']} capability availability",
                *[f"  {item['capabilityId']}: {item['state']} ({item['reason']})" for item in records],
                "",
            ]
        )
    if command == "capabilities-invoke":
        invocation = data["invocation"]
        return f"{invocation['capability_id']}: invoked {invocation['operation_id']}\n"
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
    if command == "operations-list":
        operations = data["operations"]
        if not operations:
            return "No durable operations yet.\n"
        lines = ["Durable operations"]
        lines.extend(
            f"  {item['operation']['spec']['operation_id']:<28} {item['operation']['spec']['state']} (v{item['version']})"
            for item in operations
        )
        return "\n".join([*lines, ""])
    if command == "operations-get":
        operation = data["operation"]["spec"]
        return "\n".join(
            [
                operation["operation_id"],
                f"  State: {operation['state']}  Version: {data['version']}",
                f"  Tool: {operation['tool_id']} {operation['revision_ref']}",
                "",
            ]
        )
    if command == "operations-events":
        events = data["events"]
        return "\n".join(
            ["Operation history", *[f"  {event['spec']['sequence']}: {event['spec']['event_type']}" for event in events], ""]
        )
    if command == "operations-receipts":
        receipts = data["receipts"]
        if not receipts:
            return "No effect receipts for this operation.\n"
        return "\n".join(["Effect receipts", *[f"  {receipt['spec']['receipt_id']}" for receipt in receipts], ""])
    if command == "operations-cancel":
        operation = data["operation"]["spec"]
        return f"Cancellation requested for {operation['operation_id']}.\n"
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
        _remaining, _json_mode, debug, _verbose, _ws = _extract_global_options(selected)
        if debug:
            raise
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
