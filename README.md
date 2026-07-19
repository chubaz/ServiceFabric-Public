# ServiceFabric

ServiceFabric is a canonical package and tool platform for composing, running, and governing application capabilities. The primary integration surface is its immutable package/tool definitions and canonical invocation and result contracts; consumer adapters, including MCP projections, do not own runtime behavior.

## Start with the foundation release

The current foundation release is a source-level engineering release. With Python 3.11 or newer, install and run its read-only local check:

```bash
python3 -m pip install -e packages/servicefabric_release_readiness
servicefabric doctor --repository-root .
```

`servicefabric doctor` validates the Python prerequisite and package metadata declared by the [foundation-release manifest](packages/servicefabric_release_readiness/servicefabric_release_readiness/foundation_release.json). It does not install dependencies, provision infrastructure, access secrets, or contact remote services.

Continue with the [five-minute demonstration](docs/getting-started/foundation-release.md), [product overview](docs/architecture/product-overview.md), and [foundation capability reference](docs/reference/foundation-capabilities.md).

## Find your way around

- `packages/` contains the canonical contracts and bounded implementation packages.
- `clients/python/` provides the `servicefabric` command-line interface.
- `docs/architecture/` explains the product model and recorded decisions; `docs/reference/` describes supported capabilities.
- `examples/` contains reviewed reference applications and `tests/` holds their executable acceptance and architecture boundaries.
- `config/agent/` and `docs/workplans/` record the active engineering scope and verification rules.

Before contributing, read [AGENTS.md](AGENTS.md), then run `make agent-preflight` and `make agent-context`. Validate a completed change with `make verify-current` and prepare its handoff with `make agent-handoff`.

## Maturity and boundaries

This release supports repository-local engineering and reviewable, deterministic workflows. It is not a hosted control plane or a turnkey production deployment. Distillation publication remains explicitly human-approved; legacy numbered services are compatibility context rather than the primary architecture.
