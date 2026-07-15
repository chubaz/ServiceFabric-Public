# Wave-6 Integration Handoff

## Bootstrap

Wave-6 is bootstrapped on `integration/phase2-wave6`. Projection functionality is intentionally not implemented by this commit.

## Contracts Frozen

`CapabilityDefinition`, `CapabilityRegistry`, Wave-5 availability and invocation services, AP-01A tools, and existing MCP behavior remain unchanged. Projections must delegate to `CapabilityRuntimeService` and may expose only registered capabilities.

## Verification

- `python3 -m unittest tests.agent.test_wave_06_harness -v`
- `python3 -m unittest discover -s tests/agent -v`
- `make verify-wave-06`
- `git diff --check`

The agent runtime initializer installs the existing pinned FastAPI runtime lock so generated application startup has its declared FastAPI and Uvicorn dependencies. The startup regression passes with the pre-existing subprocess cleanup warnings.

## Rollback

Revert `chore(agents): bootstrap Wave-6 consumer projections` to remove the Wave-6 coordinator harness and generated-application runtime provisioning. No projection behavior or frozen contract changes are included.
