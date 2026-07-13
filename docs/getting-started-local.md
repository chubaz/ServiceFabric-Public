# Local Developer UX

ServiceFabric provides a bounded local-only developer command. It composes the reviewed math runtime, local policy evaluator, immutable artifact store, and file-backed operation repositories. It does not start a web server or production control plane.

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r packages/servicefabric_contracts/requirements/test.lock
python3 -m pip install --no-build-isolation --no-deps \
  -e packages/servicefabric_contracts \
  -e packages/servicefabric_runtime \
  -e packages/servicefabric_governance \
  -e packages/servicefabric_operations \
  -e packages/servicefabric_artifacts \
  -e packages/servicefabric_builder \
  -e packages/servicefabric_capsules \
  -e services/tool_runtime \
  -e services/application_builder \
  -e services/capsule_host \
  -e services/governance_operations \
  -e clients/python

servicefabric init
servicefabric doctor
servicefabric tools list
servicefabric invoke math.calculate --arguments '{"expression":"1+1"}' --explain
```

`SERVICEFABRIC_HOME` selects the workspace; the default is `.servicefabric/` in the current directory. The workspace contains only local immutable artifacts, operation data, idempotency records, approvals, and configuration. The tool-runtime, application-builder, capsule-host, and governance-operation service boundaries are separately installable packages; their factories construct reviewed portfolios and local durable repositories without a `PYTHONPATH` setting.

Available commands include `status`, `doctor`, `tools`, `invoke`, `apps`, and `artifacts`. Default output is concise and task-oriented; add `--json` anywhere in a command when another tool needs deterministic structured output. Failures return nonzero without a traceback unless `--debug` is supplied.

Build output is immutable and can be found again without copying a digest from earlier output:

```bash
servicefabric apps build examples.hello-static --revision 1.0.0
servicefabric artifacts list
servicefabric artifacts verify sha256:YOUR_ARTIFACT_DIGEST
```

The reviewed hello capsule can be dispatched locally once its static artifact has been built. This is a one-shot in-process loopback session, not a public server:

```bash
servicefabric capsules dispatch \
  --request-file packages/servicefabric_contracts/tests/fixtures/capsule_host_request_hello.json \
  --method GET \
  --path /
```

The local command is intentionally limited: there is no public HTTP or MCP transport, production identity, external provider execution, deployment orchestration, or V5 control plane.
