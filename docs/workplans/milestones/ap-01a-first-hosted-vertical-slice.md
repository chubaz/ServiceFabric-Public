# AP-01A: First Hosted Vertical Slice

## Objective
Deliver the reviewed `text-utility` FastAPI application through the installed `servicefabric` command: install, build, loopback start, health, resource observation, governed capability call, and stop.

## Scope
Create a bounded local composition root, reviewed hosted-package description, managed FastAPI process adapter, resource observer, capability bridge, Text Utility example, subprocess CLI acceptance suite, and local documentation.

## Phases
1. Programme registration.
2. Reviewed hosted-package and Text Utility application.
3. Managed loopback FastAPI hosting and lifecycle.
4. Bounded process resource observation.
5. Governed application capability bridge.
6. Installed CLI journey and failure handling.
7. Subprocess acceptance and inherited verification.

## Required journey
`servicefabric apps install examples/text-utility`; `apps build text-utility`; `apps start text-utility`; `apps status text-utility`; `apps resources text-utility`; `tools list`; `tools describe text.count_words`; `call text.count_words --input '{"text":"ServiceFabric hosts applications and capabilities."}'`; `apps stop text-utility`.

## Boundaries
The CLI delegates to application, hosting, governance, operation, and gateway services. It must not call FastAPI actions directly. Hosting is loopback-only, commands come only from reviewed package definitions, and stopped applications make capabilities unavailable.

## Acceptance
Use the installed CLI in subprocess tests for install idempotency, build, real health, start/status/resources, capability execution, stop/unavailable behavior, invalid input, unexpected exit, safe errors, and JSON output. Run all V1-V4 gates plus AP-01A completion commands.

The principal completion test starts a real Text Utility process on loopback and invokes `text.count_words` only through the canonical governed bridge. Resource output keeps declared expectations separate from measured current and peak values.

## Exclusions
No AP-00 framework kits, AP-01B resource-aware scheduling, AP-02 application connections, public hosting, Kubernetes, Docker, migrations, unrestricted shell execution, or legacy dynamic Flask execution.

## Completion
AP-01A remains current and is marked completed only after the real Text Utility process journey and all verification pass.

## Rollback
Revert AP-01A commits and remove the local workspace. No database migration, public deployment, DNS, TLS, Compose, or production operation cleanup is required.
