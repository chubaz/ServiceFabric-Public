"""Reviewed, framework-neutral and framework-specific guidance fragments."""

from __future__ import annotations

from servicefabric_agent_guidance.models import GuidanceFragment


ROOT_GUIDANCE = GuidanceFragment(
    fragment_id="servicefabric-root-guidance-v1",
    path="AGENTS.md",
    content="""# Application Guidance

This application is composed from independent ServiceFabric modules. Keep module
business logic inside its module and consume other modules only through declared
interfaces or resource bindings.

## Architecture

- `application.yaml` describes the application graph.
- Each `modules/<module-id>/module.yaml` declares one module's primitive, kit,
  interfaces, resources, and lifecycle.
- Framework kits provide development and build conventions; they do not own
  application business logic.

## Development

Use the ServiceFabric application commands to validate, prepare, start, inspect,
restart, build, and stop this application. Change generated application source
as ordinary framework code; retain the manifest declarations that describe its
operational contract.
""",
)


MODULE_GUIDANCE = """# Module Guidance: {module_id}

Keep this module independently buildable and runnable through its declared
framework kit. Expose only declared interfaces, consume dependencies through
their declared contracts, and update `module.yaml` when its operational
requirements change.
"""


KIT_GUIDANCE: dict[str, str] = {
    "fastapi-service": """## FastAPI service conventions

Keep the application as ordinary FastAPI code. Provide an ASGI application at
`app:app`, preserve the declared readiness endpoint, and keep HTTP contracts at
the module boundary rather than importing another module's source.
""",
    "react-web": """## React web conventions

Keep the application as ordinary React source. Read runtime configuration from
the reviewed kit's injected environment, call declared HTTP interfaces, and
place browser assets under the framework's normal build output.
""",
    "python-worker": """## Python worker conventions

Keep the worker as ordinary Python code. Process only declared bindings, emit
useful structured logs, and handle shutdown without abandoning in-flight work.
""",
    "python-library": """## Python library conventions

Keep this module importable as a normal Python package. It has no independent
runtime process; publish the declared library interface and test it directly.
""",
}
