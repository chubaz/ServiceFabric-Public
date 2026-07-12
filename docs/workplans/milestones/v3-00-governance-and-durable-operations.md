# V3-00 — Governance and Durable Operations

## 1. Objective and vertical slice

V3-00 implements the first bounded governance and durable-operation path over the
canonical tool runtime established through V2-01:

```text
trusted canonical request
        ↓
authority and policy evaluation
        ↓
approval request where required
        ↓
immutable approval decision and binding
        ↓
durable operation acceptance
        ↓
validated persistent state transitions
        ↓
bounded execution attempt
        ↓
evidence and observed effects
        ↓
verified effect receipts or reconciliation
        ↓
terminal result, cancellation, timeout, or failure
```

Accepted durable work remains observable after the accepting process terminates.
The demonstration must submit a deterministic fixture operation, restart the local
controller, recover the operation and immutable history, and complete or reconcile
it without changing its identity or authority.

The implementation must keep request identity, invocation identity, operation
identity, policy decision, approval decision, approval binding, execution attempt,
operation state, evidence, observed effect, effect receipt, and reconciliation
record separate.

## 2. Starting conditions and governing documents

Required baseline:

```text
E0-00 completed
V1-00 completed
V1-01 completed
V2-00 completed
V2-01 completed
canonical specification hashes valid
V2-01 completion verification passing in the repository external Python environment
working tree clean before implementation
```

Read before implementation:

```text
AGENTS.md
docs/workplans/current.md
docs/workplans/status.json
docs/architecture/post-c1-execution-roadmap.md
docs/canonical/ServiceFabric Production Architecture  Roadmap.md
docs/contracts/tool-lifecycle-v1alpha1.md
docs/contracts/invocation-result-v1alpha1.md
docs/workplans/milestones/v2-01-capsule-hosting-and-authoring.md
packages/servicefabric_contracts/src/servicefabric_contracts/
packages/servicefabric_runtime/
services/tool_runtime/
clients/python/
```

Governing ADRs remain ADR-0001 through ADR-0005. In particular, MCP remains an
optional projection, package and operation identities remain distinct, legacy
execution remains contained, schema ownership remains singular, and repository
workplans own milestone execution instructions.

Before editing, run:

```bash
make agent-preflight
make agent-context
make verify-current
```

Use the repository external Python environment and editable local packages. Do not
replace missing dependencies by weakening committed checks.

## 3. Scope and exclusions

V3-00 includes:

```text
strict governance, approval, transition, attempt, idempotency and reconciliation contracts
deterministic JSON Schema snapshots and examples
bounded deterministic policy evaluation
immutable approval requests, decisions and intent bindings
file-backed local durable operation storage
append-only event history with reconstructable snapshots
validated operation state transitions and optimistic concurrency
idempotency reservation and duplicate handling
bounded execution attempts, cancellation, timeout and retry control
observed-effect verification and explicit uncertain-effect reconciliation
evidence-reference persistence and linkage
internal policy, approval, operation, idempotency and reconciliation service boundaries
Python client delegation and machine-readable CLI commands
deterministic fake policy, identity, clock, executor and effect adapters
architecture, security, recovery and V2-01 regression verification
```

V3-00 explicitly excludes:

```text
general policy languages or arbitrary policy code
production identity providers or caller authentication adapters
production approval UI or external approver federation
public multi-tenant APIs
real irreversible external effects
PostgreSQL, Django models or migrations
Redis, NATS, distributed queues or distributed schedulers
distributed workers or multi-process coordination
Kubernetes, Compose or Nginx changes
production secret-management infrastructure
remote source retrieval or arbitrary code, shell, SQL or subprocess execution
production deployment orchestration
MCP gateway, MCP server or V4 projection work
```

## 4. Existing contract inventory

Do not introduce parallel meanings for existing resources.

| Existing concept | V3-00 treatment | Rationale |
| --- | --- | --- |
| `ToolInvocationRequest` and targets | Reuse unchanged | Canonical request, arguments, target and response preference remain the input boundary. |
| `CallerContext` | Reuse unchanged | It carries verified identity assertions but is trusted only when built by an authenticated adapter. |
| `InvocationIdempotency` | Reuse unchanged | Its digest and replay intent feed the new idempotency record; raw keys remain outside canonical records. |
| `ToolInvocationAcceptance` | Reuse unchanged | It remains the durable acceptance response. |
| `ToolExecutionContext` | Extend compatibly only if an attempt needs opaque governance references not already represented | It already carries resolved revision, attenuated budget, approvals, policy decisions and credential bindings. |
| `ServiceFabricOperation` | Extend compatibly | Preserve its identity, states, timestamps, result/error and cancellation semantics; add only version or history references required for safe persistence. |
| `CancellationState` and `OperationCondition` | Reuse or compatibly strengthen | They remain the canonical observed cancellation and condition summaries. |
| `EffectDeclaration` / `EffectContract` | Reuse unchanged | Immutable prospective effects are policy inputs. |
| `ObservedEffect` | Reuse unchanged unless a correlation reference is essential | It records observed execution effects, not policy or approval. |
| `EffectReceipt` | Reuse and compose | It remains the canonical verified effect record and is linked from attempts, reconciliation and terminal results. |
| `EvidenceRecord` / evidence references | Reuse and compose | Evidence supports decisions and outcomes but never grants authority. |
| `ToolResult` / `ToolError` | Reuse unchanged | Terminal results and caller-safe failures retain the C1-02 envelope and taxonomy. |
| `PermissionContract`, approval policy references and revision reliability | Reuse unchanged | They are immutable policy inputs, not runtime decisions. |

Genuinely new resources are policy evaluation and decision records, approval request,
decision and binding records, immutable operation transition/event records,
idempotency records, execution-attempt records, and reconciliation records.

## 5. Trust and authority model

### Trusted adapter boundary

Serialized `CallerContext`, approval references or policy references do not grant
authority. A trusted adapter authenticates the caller, constructs `CallerContext`,
records the authentication-strength and authority-chain references, and submits the
canonical request to the governance service through an in-process trusted boundary.
Tests must prove that untrusted payloads cannot select the trusted constructor.

### Authority attenuation

Policy evaluation receives the verified caller, immutable resolved revision,
declared permissions and effects, deployment policy references, arguments digest,
requested budget, parent authority and environment classification. Effective scopes,
budget, tenant/resource scope and allowed effects may only remain equal or become
narrower than their trusted inputs. A child invocation cannot acquire authority not
present in its parent or a verified policy decision.

### Default deny and risk

Missing identity, unresolved revision, absent permission, unavailable policy,
unknown policy version, expired approval, changed intent or unavailable approval
authority yields denial. Risk is a bounded classification (`low`, `moderate`,
`high`, `critical`) derived from declared effects, reversibility, target scope,
caller authority and revision policy; callers cannot lower it.

### Policy outputs and binding

Every decision binds an immutable policy bundle ID and digest/version, evaluation
input digest, caller/tenant references, tool and revision, argument/intent digest,
effect classes, effective authority, constraints, decision time and validity window.
Safe explanations use stable reason codes and bounded caller-safe text. They contain
no credentials, raw arguments, policy source or internal paths.

## 6. Canonical governance resources

All resources use `servicefabric.ai/v1alpha1`, strict unknown-field rejection,
bounded collections and deterministic draft 2020-12 schemas. Operational timestamps
are timezone-aware; digests are SHA-256; immutable records use immutable models.

### `PolicyEvaluationRequest`

- Identity: evaluation request ID, distinct from invocation and operation IDs.
- Mutability: immutable.
- Fields: caller reference/context digest, request and intent digests, tool/revision,
  declared effects and permissions, requested budget, parent decision references,
  environment and policy-set references.
- Invariants: immutable revision only; trusted-context marker is internal service
  input and cannot be asserted by public deserialization; no raw arguments or secrets.
- Retention/references: retained with its `PolicyDecision` and operation history.
- Security: safe digests and opaque references only.

### `PolicyDecision`

- Identity: decision ID.
- Mutability: immutable.
- Fields: request reference, outcome (`allow`, `deny`, `require_approval`,
  `constrained_allow`), policy bundle ID/version/digest, reason codes, risk,
  effective authority and budget constraints, required approval policy/effect scope,
  issued/expiry times and evaluator provenance.
- Invariants: deny grants no authority; constrained allow only attenuates; approval
  outcome names an approval policy; expiry follows issue time; exact input digest binds.
- Retention/references: retained at least as long as related operations, approvals,
  evidence and receipts.
- Security: immutable, caller-safe explanation; no executable policy payload.

### `ApprovalRequest`

- Identity: approval request ID.
- Mutability: immutable request; pending/expiry is derived from immutable decisions
  and current time, not edited into the request.
- Fields: policy decision, operation/request/caller/tool/revision refs, intent digest,
  effect scope and risk, requested authority, reason, created/expiry times.
- Invariants: exact immutable revision and policy decision; non-empty approval scope;
  expiry bounded; no approver decision embedded.
- Retention/references: retained with every decision and binding.

### `ApprovalDecision`

- Identity: decision ID.
- Mutability: immutable.
- Fields: approval request, outcome (`approved`, `denied`, `expired`, `revoked`),
  approver subject and authority references, decision time, reason code, validity end,
  policy decision and intent digests.
- Invariants: only trusted approval service records a decision; one active approval
  decision per request; revocation references the prior approval rather than mutating it.
- Retention/references: never deleted while a binding or operation references it.
- Security: approver serialization alone is not authority; no tokens or signatures.

### `ApprovalBinding`

- Identity: binding ID.
- Mutability: immutable, single intent; consumption is a separate event/record.
- Fields: approved decision, policy decision/version, caller and tenant, operation,
  tool/revision, arguments/request-intent digest, effect scope, authority constraints,
  validity window, single-use policy and binding digest.
- Invariants: every bound value exactly matches the governed operation; changed
  arguments, revision, caller, effects, policy version or budget invalidates it.
- Retention/references: retained with attempts, transitions and receipts.
- Security: cannot broaden policy authority or outlive its decision.

### `OperationTransition` and `OperationEvent`

Use `OperationTransition` as the immutable canonical state change and a small
`OperationEvent` envelope for ordered persistence metadata if storage replay requires
it. Do not duplicate `ServiceFabricOperation` as a second mutable status model.

- Identity: event ID and operation-local monotonically increasing version.
- Mutability: immutable append-only.
- Fields: operation, prior/new state, expected/new version, occurred time, actor,
  reason, condition/result/error/cancellation references, policy/approval/attempt/
  evidence/effect references and event digest chained to the previous digest.
- Invariants: legal transition, exact prior version/state, one event per version,
  deterministic digest chain, no history replacement.
- Retention/references: event history is authoritative; snapshots are rebuildable.

### `IdempotencyRecord`

- Identity: scope plus canonical key digest.
- Mutability: controlled state transitions (`reserved`, `in_progress`, `completed`,
  `failed`, `expired`) with immutable history.
- Fields: key digest, request-intent digest, caller/tenant/tool/deployment scope,
  operation and result refs, reservation/version, creation/expiry.
- Invariants: raw key absent; same key and same intent returns existing outcome;
  same key with different intent is a conflict; atomic first reservation wins.
- Retention/references: retained through configured replay window and never shorter
  than uncertain-effect reconciliation needs.

### `ExecutionAttempt`

- Identity: attempt ID plus operation-local attempt number.
- Mutability: immutable completion record; start and finish are append-only events.
- Fields: operation/invocation/revision/context refs, number, start/end, outcome,
  error classification, retry eligibility, budget consumed, evidence/effect refs.
- Invariants: positive contiguous attempt number; one active attempt per operation;
  bounded maximum; immutable execution context; uncertain effects block retry.
- Retention/references: retained with operation and receipts.

### `ReconciliationRecord`

- Identity: reconciliation ID.
- Mutability: immutable record per attempt.
- Fields: operation/attempt/declared effect, observed effects, provider operation ref,
  prior uncertainty, verification method/outcome, evidence and receipt refs, time.
- Invariants: no provider credential or payload; terminal reconciliation outcome is
  known committed, known absent, still unknown, reversed or failed; retries unlock
  only after known-absent or policy-approved safe outcome.
- Retention/references: retained with effect receipt and operation history.

## 7. Policy evaluation semantics

The initial evaluator is deterministic and allowlist-based. It accepts reviewed,
versioned policy fixtures expressed as bounded data; it does not interpret Python,
expressions, templates or a general policy language.

Outcomes:

```text
allow               exact requested authority is allowed
constrained_allow   authority or budget is attenuated
deny                execution is prohibited
require_approval    execution waits for an exact approval binding
```

Evaluation order is stable: validate trusted context, resolve policy bundle version,
validate tenant/resource authority, classify effects/risk, apply deny rules, derive
approval requirements, attenuate constraints, emit decision. Conflicting rules use
deny-overrides. Missing/unreadable/corrupt policy data, unknown effect classes or
unavailable evaluator fail closed with a caller-safe policy error. Decisions bind
the exact policy digest so later policy changes require reevaluation and cannot
retroactively alter history.

## 8. Approval lifecycle

1. A `require_approval` decision creates one immutable `ApprovalRequest` and moves
   the operation to `waiting_for_approval`.
2. The bounded approval service validates trusted approver authority against the
   request policy and records exactly one immutable decision.
3. `approved` creates an immutable `ApprovalBinding`; `denied` fails or cancels the
   operation according to stable policy; elapsed validity produces `expired`.
4. Revocation is a new immutable decision referencing an approval. It prevents new
   attempts; an already committed effect is not undone.
5. Before every protected attempt, the controller verifies caller, tenant, operation,
   tool/revision, intent digest, effect scope, policy decision/version, validity and
   single-use status. Any mismatch fails closed.

There is no production UI or identity provider. Tests use deterministic trusted
approver fixtures and prove serialized approver fields cannot forge authority.

## 9. Durable operation state machine

Terminal states are `succeeded`, `partially_succeeded`, `failed`, `cancelled` and
`timed_out`. Terminal operations cannot transition again.

| From | Legal destinations | Preconditions |
| --- | --- | --- |
| accepted | queued, waiting_for_approval, failed, cancelled, timed_out | Policy decision recorded; approval state determines queue eligibility. |
| waiting_for_approval | queued, failed, cancelled, timed_out | Exact valid binding for queued; denial/expiry reason for failed; cancellation persisted. |
| queued | running, waiting_for_dependency, cancelled, timed_out, failed | Version matches; approval remains valid; attempt budget remains. |
| waiting_for_dependency | queued, running, cancelled, timed_out, failed | Dependency readiness or bounded retry time reached. |
| waiting_for_human | queued, cancelled, timed_out, failed | Required human record exists and authority remains valid. |
| running | succeeded, partially_succeeded, failed, cancelled, timed_out, waiting_for_dependency, waiting_for_human | Attempt closes; result/effect/cancellation invariants hold; uncertain effects require reconciliation before requeue. |

Illegal examples include skipping required approval, `accepted → succeeded`,
`queued → succeeded` without an attempt, transitions from terminal states, decreasing
versions, changing operation identity, or replacing prior events.

Every transition compares expected operation version and prior state, appends one
immutable transition, then atomically replaces the derived snapshot. Timestamps are
timezone-aware and non-decreasing. Terminal states require `completed_at`; success
cannot contain a primary error; failure requires `ToolError`; cancelled/timed-out
states require reasons. Recovery replays events, verifies the digest chain, and
returns interrupted `running` work to a recovery decision: retry only if safely
retryable and effects are known absent, otherwise wait for reconciliation or fail.

## 10. Durable local storage

Create a first-class framework-neutral package behind repository interfaces, with a
file-backed adapter suitable only for local single-process operation.

Required properties:

- Repository-controlled root supplied by the caller; canonical resources never
  contain paths.
- Validated opaque IDs map to fixed digest-based filenames; no path traversal,
  symlink escape or caller-selected filename.
- Deterministic UTF-8 JSON, sorted keys, final newline and bounded record/event sizes.
- Atomic publication through same-directory temporary file, flush, `fsync`, rename
  and parent-directory sync where supported.
- Compare-and-swap operation versions under an in-process lock and exclusive local
  lock where safely portable; conflicts are explicit.
- Append-only immutable event files or segments plus an atomically replaced snapshot.
- SHA-256 content and previous-event digest validation on every read/replay.
- Startup recovery ignores no corruption: invalid/missing/gapped events quarantine
  the operation from execution and return a safe corruption error.
- Explicit maximum operations, events per operation, bytes per record, attempts,
  evidence refs and retention age. Retention refuses deletion while approvals,
  idempotency records, effects or reconciliation still reference the operation.

No database, remote store, queue or distributed locking is introduced.

## 11. Event history and replay

Use snapshots plus immutable ordered transition events. The event stream is
authoritative; snapshots are acceleration only.

- Version starts at 1 for acceptance and increments exactly once per event.
- Event ordering is operation-local version order, not filesystem or timestamp order.
- Each event includes the prior digest and its own canonical digest.
- Replay validates operation ID, sequence, prior state, transition legality, digest
  chain and snapshot equality.
- A missing, duplicate, malformed or altered event marks the operation corrupt and
  prevents execution; repair is outside this milestone.
- Snapshot reconstruction from events must produce byte-equivalent canonical state.
- Events are immutable and never compacted in V3-00.

## 12. Idempotency and duplicate handling

Only a trusted adapter may hash the raw idempotency key. The canonical digest combines
a domain separator, normalized scope and key through SHA-256. The separate request-
intent digest covers caller/tenant, tool, immutable revision or deployment resolution,
canonical arguments, requested response mode and effect-relevant constraints.

Atomic reservation behavior:

```text
new key + intent             reserve and create one operation
same key + same in progress  return the existing acceptance/operation
same key + same completed    return the existing terminal result reference
same key + different intent  reject with conflict; create nothing
concurrent identical calls   one wins; all others resolve to the same operation
```

Raw keys never enter logs, errors, events, receipts or public records. Retention is a
reviewed bounded policy and cannot expire while an effect is uncertain or within the
tool's duplicate-delivery protection window.

## 13. Execution attempts, cancellation, timeout and retry

An operation is durable intent; an attempt is one bounded execution try. Attempt
numbers start at 1, are contiguous, and never exceed the revision/policy retry budget.
The controller records start before delegation and completion afterward.

Retry eligibility combines revision reliability declarations, policy constraints,
error category, remaining budget, deadline, cancellation and effect certainty.
Backoff is represented as deterministic bounded duration and next-eligible time;
tests use a fake clock and perform no sleeps.

Cancellation is cooperative. The request is persisted before signalling an adapter;
acknowledgement and completion are later transitions. Cancellation never claims to
reverse committed effects. A deadline or maximum duration persists a timeout reason;
if the attempt may have produced an effect, the operation enters reconciliation
handling before any retry. Retryable errors are not automatically effect-safe.

No retry occurs after an uncertain effect until reconciliation establishes known
absence or another explicitly policy-approved safe state.

## 14. Effect verification and reconciliation

Declared `EffectContract` describes prospective policy inputs. `ObservedEffect`
records execution observations. `EffectReceipt` records verification. A
`ReconciliationRecord` explains resolution of uncertainty; none substitutes for
another.

| Situation | Required behavior |
| --- | --- |
| Timeout before adapter starts | Record known absent/no attempt effect; retry may follow bounded policy. |
| Timeout after dispatch, no provider result | Record unknown observed effect; block retry and require reconciliation. |
| Provider confirms commit | Persist observed committed effect and verified receipt before terminal success. |
| Provider confirms no effect | Persist verified no-op/known-absent evidence; bounded retry may proceed. |
| Outcome remains unknown | Preserve uncertainty, expose reconciliation-required condition, do not retry. |
| Verification unavailable | Fail closed for required verification; keep operation non-successful and reconcilable. |

V3-00 uses deterministic local fake effect adapters only. Reconciliation reads a
bounded provider-operation reference, emits evidence, observed effects and a receipt
or unresolved record, and cannot execute arbitrary repair logic.

## 15. Evidence persistence

Evidence is stored through a bounded evidence repository as immutable records or
opaque references. Policy decisions, approval decisions, transitions, attempts,
results, receipts and reconciliation records list explicit evidence references.
The store verifies IDs and digests, enforces size/count limits and retains evidence
for at least the lifetime of referencing operation history.

Evidence supports audit and verification but never modifies caller identity,
permissions, policy outcome or approval authority. External/fake-provider evidence
retains its trust classification. Raw arguments, credentials and unrestricted source
bodies are not persisted as evidence.

## 16. Internal packages and service boundaries

Expected dependency direction:

```text
servicefabric_contracts
        ↑
governance domain interfaces and deterministic policy/approval logic
        ↑
operation controller and idempotency/reconciliation orchestration
        ↑
file-backed persistence adapters and fake execution/effect adapters
        ↑
internal service facade
        ↑
Python client and CLI
```

Suggested first-class packages may include `servicefabric_governance` and
`servicefabric_operations`; exact naming is decided during `governance-contracts`
without merging domain and persistence concerns. Canonical packages import no web
framework or persistence adapter. Client code calls the internal service facade and
never opens storage files.

Bounded interfaces:

- Policy evaluator: immutable input to immutable decision.
- Approval service: request, trusted decision recording, binding validation.
- Operation repository/controller: acceptance, query, transition, recovery, events.
- Idempotency repository: reserve, resolve, complete and conflict.
- Reconciliation service: inspect uncertain effects and record bounded outcome.
- Evidence repository: publish and resolve immutable evidence.

## 17. Python client and CLI

Add typed client delegation and deterministic JSON CLI operations for:

```text
policy evaluate
operation submit
operation get
operation events
approval request
approval decide
operation cancel
operation resume
operation reconcile
operation receipts
```

Commands accept canonical JSON files or bounded scalar identifiers, emit one
machine-readable JSON document, use stable exit codes, and redact credentials and raw
idempotency keys. `resume` only asks the controller to re-evaluate eligibility. The
client cannot transition state, forge approval, bypass policy, or access store paths.

## 18. Demonstration vertical slice

Use a deterministic fixture tool such as `project.create_review_task`, backed by an
in-memory/fake local task provider. It declares a reversible `task_create` effect,
keyed idempotency and approval for high-risk fixture arguments.

The demonstration and tests cover:

1. low-risk allow and high-risk denial;
2. approval-required submission, trusted approval and exact binding;
3. durable acceptance followed by process/controller reconstruction and recovery;
4. duplicate submission returning the same operation and conflicting reuse failing;
5. successful attempt with observed effect, evidence and verified receipt;
6. persisted cooperative cancellation and timeout;
7. timeout after possible commit, retry prohibition, deterministic reconciliation;
8. changed arguments invalidating the approval binding.

No real external service or irreversible action is used.

## 19. Architecture and security guardrails

Tests must prevent:

```text
caller-supplied trusted authority or policy outcomes
approval forgery or changed-intent approval reuse
illegal transitions, version rollback or event-history rewriting
unbounded attempts, sleeps or retries
retry before uncertain-effect reconciliation
raw idempotency-key, credential, argument or internal-path exposure
arbitrary policy/code evaluation, shell, SQL or subprocess execution
remote source or provider retrieval
client access to persistence implementation or files
framework imports in canonical/domain packages
database models, migrations, Compose or Nginx changes
MCP gateway, server or projection implementation
```

Allowed-path enforcement must include only new governance/operation packages,
services, clients, schemas, portfolio fixtures, tests, workplans and CI needed by
V3-00. Existing legacy runtime and production topology remain untouched.

## 20. Testing strategy

Focused suites must cover:

- Strict contracts, unknown-field rejection, immutable decisions, stable digests,
  deterministic schemas and examples.
- Policy allow, constrained allow, deny, require-approval, deny precedence,
  unavailable/corrupt policy and authority attenuation.
- Approval creation, trusted decisions, exact binding, expiration, revocation,
  single-use behavior, changed-intent invalidation and forgery rejection.
- Every legal state transition and representative illegal transitions, terminal
  invariants, optimistic concurrency conflicts and timestamp/version checks.
- Atomic publication, event replay, restart recovery, snapshot reconstruction,
  corruption/gap/digest detection, path safety and retention limits.
- Idempotent duplicate acceptance/completion, conflicting reuse and concurrent races.
- Cancellation persistence/acknowledgement, timeout, bounded retry, fake-clock backoff,
  attempt history and uncertain-effect retry prohibition.
- Effect receipts, verified no-op, known/unknown outcomes, reconciliation and evidence
  linkage.
- Service and client delegation, CLI JSON output/redaction, no direct storage access.
- Architecture boundaries and complete V2-01 regression verification.

Tests require no network, Docker, database, external process, paid provider or real
irreversible effect. Temporary durable stores live outside the repository.

## 21. Verification configuration

V3-00 readiness remains the V2-01 completion gate plus workplan, architecture and
dependency-lock validation. Completion checks in `config/agent/milestones.json`
remain `planned: true` until each implementation suite exists, but every check has a
valid command array.

Required completion check names:

```text
v3-00-contracts
v3-00-policy
v3-00-approvals
v3-00-operations
v3-00-idempotency
v3-00-reconciliation
v3-00-service-client
v3-00-boundaries
schema-snapshots
dependency-locks
architecture-guardrails
v2-01-regressions
compileall
diff-check
```

Before completion, remove every `planned: true`, install first-class local packages
in the external environment, run every command explicitly, then run:

```bash
python3 scripts/agent/validate_workplans.py
make agent-preflight
make agent-context
python3 scripts/agent/verify.py --milestone v3-00 --phase completion
make verify-current
make agent-handoff
git diff --check
```

## 22. Implementation phases

Execute sequentially; run focused tests, update status and commit each phase before
starting the next.

1. `governance-contracts`: inventory/reuse existing contracts; add strict governance,
   approval, transition, attempt, idempotency and reconciliation resources, schemas,
   examples and contract tests.
2. `policy-evaluation`: implement deterministic versioned allowlist policies,
   default deny, risk classification and authority attenuation.
3. `approval-lifecycle`: implement immutable requests/decisions/bindings, trusted
   decision boundary, expiry/revocation and exact-intent validation.
4. `durable-operation-store`: implement atomic file-backed records, immutable event
   history, snapshots, optimistic concurrency, replay and recovery.
5. `operation-state-machine`: implement the legal transition matrix, preconditions,
   terminal invariants and controller recovery decisions.
6. `idempotency-and-deduplication`: implement atomic reservation, intent conflicts,
   duplicate responses and retention.
7. `cancellation-timeout-and-retry`: implement persisted cooperative cancellation,
   deadline handling, attempts, fake-clock backoff and bounded retry.
8. `reconciliation-and-effect-verification`: implement evidence linkage, observed
   effects, verified receipts and uncertain-outcome reconciliation.
9. `service-client-and-cli`: add internal facades, typed client delegation and bounded
   JSON CLI operations.
10. `cross-boundary-verification`: complete integration/restart tests, V2 regressions,
    architecture tests, locks, schemas, compileall and handoff.

## 23. Suggested commit sequence

```text
feat: add governance and approval contracts
feat: add deterministic policy evaluation
feat: add bounded approval lifecycle
feat: add durable operation store
feat: enforce operation state transitions
feat: add idempotency and duplicate handling
feat: add cancellation timeout and bounded retry
feat: add effect reconciliation
feat: add governance operations client and CLI
test: verify V3-00 integration boundaries
docs: complete V3-00 milestone status
```

## 24. Acceptance criteria

V3-00 is complete only when:

- Contracts reuse the C1 operation, caller, request, result, evidence and effect
  semantics; all new schemas and examples are deterministic and strict.
- Policy evaluation deterministically produces all four outcomes, binds an immutable
  policy version, attenuates authority and fails closed when unavailable.
- Approval decisions/bindings are immutable, trusted, expiring and bound to exact
  caller, operation, revision, intent, policy and effect scope.
- Every allowed state transition succeeds and every illegal transition fails without
  changing history; optimistic concurrency rejects stale writers.
- Accepted operations, snapshots, events, decisions, attempts, evidence and receipts
  survive controller restart and replay with corruption detection.
- Duplicate requests resolve atomically to one operation; conflicting key reuse is
  rejected; raw keys are absent from records and output.
- Cancellation and timeout are persisted; attempts and retries are bounded; uncertain
  effects cannot retry before reconciliation.
- Known committed/absent and unknown effects produce correct observed effects,
  evidence, receipts and reconciliation records.
- Service, client and CLI delegate through boundaries and never manipulate storage.
- The deterministic vertical slice demonstrates allow, deny, approval, restart,
  duplicate, success, cancellation, timeout and reconciliation without external I/O.
- All named completion checks pass with exact test counts reported; V2-01 remains
  passing; no forbidden runtime/topology/migration files change.

## 25. Stop conditions

Stop and report if implementation requires a production identity provider, general
policy language, real irreversible effect, distributed coordination, database,
migration, topology change, MCP work, raw secret/idempotency storage, arbitrary code
execution, history mutation, weakening an existing contract invariant, or retrying an
uncertain effect without reconciliation.

## 26. Known limitations

```text
local single-process coordination
local durable storage only
no production identity provider
no production approval UI
no public multi-tenant service
no PostgreSQL
no distributed event bus
no distributed scheduler
no Kubernetes
no production secrets platform
no real irreversible external effects
no V4 MCP projection
```

The local durability design proves boundaries and recovery semantics; it is not the
final production topology.

## 27. Rollback

Revert the V3-00 commits and remove local test operation data from explicitly
configured temporary/store directories. No database, Compose, Nginx, Kubernetes,
DNS, TLS or production-effect cleanup is required.

## 28. Completion report

The implementation agent must report:

```text
Blockers
Changed areas
Contract inventory
Policy behavior
Approval behavior
Durability and recovery
Idempotency results
Cancellation and retry results
Reconciliation results
Security and architecture guardrails
Validation and exact test counts
Deviations
Known limitations
Rollback
Next-session prompt
```

At branch completion, keep V3-00 current with phase `completed` until merge and
handoff. Do not implement V4-00 in this milestone.
