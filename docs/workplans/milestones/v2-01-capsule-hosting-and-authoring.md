# V2-01 — Capsule Hosting and Authoring

## 1. Objective

Implement the first bounded ServiceFabric capsule-authoring and capsule-hosting vertical slice.

V2-01 must allow ServiceFabric to:

```text
accept a reviewed capsule definition
        ↓
resolve immutable application artifacts
        ↓
validate capsule composition and routes
        ↓
produce an immutable capsule revision
        ↓
open a bounded local host session
        ↓
serve declared routes and assets
        ↓
record deterministic session evidence
        ↓
close the session cleanly
```

A capsule is a reviewed composition that binds one or more immutable ServiceFabric application artifacts to a bounded presentation and routing model.

V2-01 is not:

```text
a production deployment platform
a public web-hosting service
a general application server
a container orchestrator
a dynamic backend runtime
an unrestricted authoring environment
a database-backed content-management system
```

The milestone must preserve the V2-00 guarantees around immutable application revisions, reproducible artifacts, content-addressed storage, path safety, and bounded local preview.

---

# 2. Starting conditions

Start from the merged V2-00 milestone.

Required baseline:

```text
E0-00 completed
V1-00 completed
V1-01 completed
V2-00 completed
V2-01 current
working tree clean
canonical specification hashes valid
V2-00 completion verification passing
application builder packages installable
artifact store packages installable
```

Before editing, run:

```bash
make agent-preflight
make agent-context
make verify-current
```

At the beginning of V2-01, completion checks may remain marked as planned.

Before merging V2-01:

```text
all planned completion checks must be replaced
all completion commands must be executable
all required checks must pass
all V2-00 regression checks must continue to pass
capsule hosting must remain bounded and local
handoff to V3-00 must be generated
```

---

# 3. Governing principles

## 3.1 Immutable composition

A capsule revision is immutable.

Its identity must be derived from canonical reviewed inputs, including:

```text
capsule definition identity
capsule revision
bound application artifact digests
route declarations
entry route
mount declarations
host policy revision
authoring manifest
```

Its identity must not depend on:

```text
creation timestamp
temporary directory
host name
process identifier
ephemeral port
session identifier
absolute filesystem location
random identifier
log ordering
```

Equivalent canonical inputs must produce the same capsule revision digest.

## 3.2 Artifacts remain authoritative

Capsules must reference immutable V2-00 artifacts by digest.

Capsules must not reference:

```text
mutable application branches
latest revisions
unversioned application names
temporary build directories
host filesystem paths
remote URLs
live source directories
```

A capsule host must read artifact files through the canonical artifact boundary.

It must not bypass the artifact store and directly traverse build workspaces.

## 3.3 Separation of definition, revision, authoring and hosting

Keep these concepts distinct:

```text
CapsuleDefinition
    stable reviewed identity and descriptive metadata

CapsuleRevision
    immutable reviewed composition

CapsuleAuthoringManifest
    bounded authoring input used to produce a revision

CapsuleHostRequest
    request to open one bounded host session

CapsuleHostSession
    temporary runtime presentation of one immutable revision

CapsuleHostResult
    canonical result and evidence for opening or closing a session
```

Do not collapse these concepts into a single mutable capsule object.

## 3.4 Authoring is declarative

V2-01 authoring means creating and validating canonical capsule resources.

Authoring must not include:

```text
arbitrary source editing
shell execution
package installation
Git operations
remote source retrieval
code generation through unreviewed templates
arbitrary file uploads
direct artifact mutation
```

The initial authoring boundary may accept only a bounded structured manifest.

## 3.5 Hosting is bounded presentation

The capsule host owns only:

```text
revision resolution
artifact verification
route resolution
asset serving
session lifecycle
loopback binding
request limits
response limits
evidence collection
clean shutdown
```

It must not execute application JavaScript on the server, invoke subprocesses, run backend code, mutate artifacts, or persist user state.

## 3.6 Default deny

Anything not explicitly declared by the capsule revision must be unavailable.

This includes:

```text
undeclared routes
undeclared artifacts
undeclared files
directory listings
filesystem traversal
implicit index fallback
cross-capsule access
remote proxying
runtime environment exposure
```

---

# 4. Governing documents

Read:

```text
AGENTS.md
docs/workplans/current.md
docs/workplans/status.json

docs/architecture/adr/
docs/contracts/
docs/refactoring/programme.md
docs/architecture/post-c1-execution-roadmap.md

docs/workplans/milestones/v2-00-immutable-application-builder.md

packages/servicefabric_contracts/
packages/servicefabric_builder/
packages/servicefabric_artifacts/
services/application_builder/
clients/python/
portfolio/
schemas/servicefabric/
```

Preserve the V2-00 distinctions between:

```text
application definition
application revision
application artifact
artifact storage
preview session
```

Do not change canonical architectural decisions unless a real conflict is found and documented through an ADR.

---

# 5. Scope

V2-01 includes:

```text
capsule definition contracts
capsule revision contracts
capsule authoring manifest
capsule route contracts
capsule artifact bindings
capsule host request and result contracts
host-session contracts
file-backed capsule portfolio
bounded declarative authoring
deterministic capsule identity
route and asset validation
loopback-only capsule host
session lifecycle management
request and response limits
Python client support
bounded CLI support
host evidence and diagnostics
tests and architecture guardrails
```

V2-01 excludes:

```text
production deployment
public internet exposure
TLS termination
domain management
load balancing
reverse proxy configuration
container orchestration
Dockerfile execution
Compose changes
Nginx changes
Django migrations
dynamic backend services
server-side JavaScript execution
Python application execution
database-backed applications
database-backed capsule registry
persistent user sessions
authentication platform implementation
multi-tenant public hosting
remote artifact stores
remote source retrieval
live code editing
browser-based authoring UI
collaborative authoring
deployment approvals
durable operations
job queues
distributed workers
MCP capsule projection
```

Governance, approval workflows, durable operations, and persistent operation tracking belong to V3-00.

---

# 6. Initial supported capsule model

V2-01 supports exactly one capsule type:

```text
static_capsule
```

A `static_capsule` consists of:

```text
one immutable capsule revision
one or more immutable static-web application artifacts
one declared entry route
a bounded set of route declarations
a bounded set of artifact mount declarations
optional capsule-owned static metadata
one reviewed host policy
```

The initial implementation may compose multiple static artifacts under distinct route prefixes.

Example:

```text
/
    artifact: examples.hello-static
    file: index.html

/docs/
    artifact: examples.docs-static
    file: index.html

/assets/main.css
    artifact: examples.hello-static
    file: assets/main.css
```

V2-01 must not:

```text
merge files from artifacts into a mutable workspace
rewrite artifact contents
execute build steps
serve files not declared by artifact manifests
proxy remote content
generate routes dynamically
```

---

# 7. Expected implementation areas

Expected additions may include:

```text
packages/
├── servicefabric_contracts/
│   └── capsule and host-session contracts
├── servicefabric_capsules/
│   ├── portfolio
│   ├── validation
│   ├── identity
│   ├── authoring
│   └── routing
├── servicefabric_builder/
│   └── read-only integration where required
└── servicefabric_artifacts/
    └── read-only artifact access where required

services/
└── capsule_host/
    ├── service boundary
    ├── host session lifecycle
    └── loopback HTTP adapter

clients/
└── python/
    └── capsule and host-session operations

portfolio/
└── capsules/
    ├── definitions/
    ├── revisions/
    ├── authoring/
    └── examples/

schemas/
└── servicefabric/
    └── capsule schemas

tests/
├── capsules/
├── capsule_host/
├── authoring/
├── routing/
└── architecture/
```

Use different paths where repository conventions clearly require them.

Do not reorganize existing V1 or V2-00 code merely to match this conceptual layout.

---

# 8. Phase 1 — Capsule contracts

## 8.1 CapsuleDefinition

Add a strict canonical `CapsuleDefinition`.

Suggested fields:

```text
api_version
kind
metadata
spec
```

Suggested `spec` fields:

```text
capsule_id
display_name
description
capsule_type
status
labels
annotations
owner_ref
```

Constraints:

```text
capsule_id must be stable and validated
capsule_type must initially equal static_capsule
unknown fields must be rejected
definitions must not contain raw artifact contents
definitions must not contain credentials
definitions must not contain host paths
definitions must not contain ephemeral session data
```

## 8.2 CapsuleRevision

Add an immutable `CapsuleRevision`.

Suggested fields:

```text
capsule_id
revision
capsule_type
authoring_manifest_digest
artifact_bindings
routes
entry_route
host_policy_ref
revision_digest
provenance
status
```

A revision must reference immutable artifact digests.

Reject:

```text
application names without revisions
mutable labels
latest aliases
temporary artifact paths
host filesystem locations
remote URLs
implicit artifact selection
```

## 8.3 CapsuleArtifactBinding

Define a strict artifact binding.

Suggested fields:

```text
binding_id
application_id
application_revision
artifact_digest
mount_path
entry_document
required
```

Constraints:

```text
artifact_digest must be canonical and validated
mount_path must be absolute URL-path syntax
mount_path must not contain traversal
mount paths must not overlap ambiguously
binding IDs must be unique
artifact files remain immutable
```

## 8.4 CapsuleRoute

Define a bounded route declaration.

Suggested fields:

```text
route_id
path
binding_id
artifact_path
media_type
fallback_policy
cache_policy
```

For V2-01:

```text
route path must be explicit
route path must be normalized
artifact_path must exist in the bound artifact manifest
fallback_policy must initially be none or declared_entry_document
wildcard routing must be excluded or sharply bounded
redirects must be excluded unless explicitly reviewed
external redirects must be prohibited
```

## 8.5 CapsuleAuthoringManifest

Define declarative authoring input.

Suggested fields:

```text
capsule_id
target_revision
bindings
routes
entry_route
host_policy_ref
author_ref
source_digest
```

The manifest must not permit:

```text
commands
scripts
environment variables
Dockerfiles
package managers
remote repositories
arbitrary files
template execution
custom Python callbacks
custom route handlers
```

## 8.6 CapsuleHostPolicy

Define a trusted host policy.

Suggested fields:

```text
policy_id
revision
bind_mode
allowed_hosts
maximum_routes
maximum_bindings
maximum_requests
maximum_request_path_bytes
maximum_response_bytes
maximum_session_seconds
idle_timeout_seconds
allowed_methods
allowed_media_types
security_headers
```

For V2-01:

```text
bind_mode must equal loopback
allowed methods must initially be GET and HEAD
request bodies must be rejected
directory listing must be disabled
range requests may be excluded
compression may be excluded
CORS must use a fixed reviewed policy
```

Application authors must not be able to widen trusted host limits.

## 8.7 CapsuleHostRequest

Define a canonical request containing:

```text
request_id
capsule_id
capsule_revision
caller_context
host_policy_ref
requested_port
correlation metadata
```

`requested_port` may permit:

```text
0
an explicitly bounded loopback port
```

It must not permit privileged ports or arbitrary interface binding.

## 8.8 CapsuleHostSession

Define a temporary host-session representation.

Suggested fields:

```text
session_id
capsule_id
capsule_revision
capsule_digest
host
port
base_url
status
opened_at
expires_at
request_budget
requests_served
artifact_digests
```

Session identity may be ephemeral.

Session identity must not influence capsule revision identity.

## 8.9 CapsuleHostResult

Define a canonical result containing:

```text
status
session
warnings
errors
evidence
metrics
effect_receipts
```

Use existing result, error, evidence, and effect conventions.

Do not create a parallel incompatible result model.

## 8.10 Schema export

Export deterministic JSON Schemas for all canonical capsule contracts.

Update:

```text
schema package exports
schema index
schema snapshots
contract fixtures
dependency locks where required
```

Acceptance criteria:

```text
strict validation
unknown-field rejection
deterministic schema output
stable serialization
round-trip fixture validation
invalid fixture coverage
```

---

# 9. Phase 2 — Capsule portfolio

## 9.1 File-backed resources

Add file-backed portfolio locations for:

```text
capsule definitions
capsule revisions
capsule authoring manifests
host policies
```

Do not introduce a database registry.

## 9.2 Example capsule

Add one reviewed example capsule, such as:

```text
examples.hello-capsule
```

It should bind the existing reviewed static-web artifact produced from:

```text
examples.hello-static
```

The example should declare:

```text
one capsule definition
one immutable revision
one artifact binding
one entry route
one or more explicit asset routes
one bounded host policy
```

It must require no network access or external CDN.

## 9.3 Resolution

The capsule portfolio resolver must:

```text
resolve definition by capsule ID
resolve immutable revision
resolve authoring manifest
resolve host policy
verify revision digest
verify referenced artifact digests
reject missing resources
reject mutable references
reject duplicate revisions
reject unknown bindings
```

Resolution order must be deterministic.

---

# 10. Phase 3 — Declarative authoring model

## 10.1 Authoring boundary

Implement a bounded authoring operation that accepts a reviewed `CapsuleAuthoringManifest`.

The operation must:

```text
validate capsule identity
resolve referenced application artifacts
verify artifact integrity
normalize routes
normalize mount paths
validate route-to-file mappings
validate host policy
calculate canonical authoring digest
produce an immutable CapsuleRevision
```

The operation must not:

```text
build applications
modify artifacts
read arbitrary source directories
run shell commands
make network requests
write outside the capsule portfolio staging area
```

## 10.2 Deterministic normalization

Normalize:

```text
capsule identifiers
revision identifiers
URL paths
mount paths
route ordering
binding ordering
header names
media types
policy references
```

Do not derive canonical identity from user-provided ordering where semantic ordering is irrelevant.

## 10.3 Authoring diagnostics

Return structured diagnostics for:

```text
duplicate routes
overlapping mounts
missing artifacts
missing files
invalid entry route
unsupported media type
invalid path
policy violation
digest mismatch
unknown binding
route shadowing
```

Diagnostics must be deterministic and machine-readable.

## 10.4 Publication

Publish a capsule revision only after all validation succeeds.

Publication must be atomic.

A failed authoring operation must not leave a partially published revision.

An identical revision may be reused.

A different revision must not overwrite an existing immutable revision.

---

# 11. Phase 4 — Capsule identity

## 11.1 Canonical digest input

Calculate capsule revision identity from a canonical structure containing:

```text
capsule ID
capsule revision
capsule type
sorted artifact bindings
artifact digests
sorted routes
entry route
host policy ID and revision
authoring manifest digest
canonical format revision
```

Exclude:

```text
timestamps
temporary paths
session IDs
ports
host names
process IDs
random identifiers
logs
runtime counters
```

## 11.2 Reproducibility tests

Tests must prove:

```text
equivalent authoring manifests produce identical revision digests
different input ordering does not change digest where ordering is non-semantic
a one-byte artifact digest change changes capsule digest
a route change changes capsule digest
a host-policy revision change changes capsule digest
temporary directory changes do not affect digest
```

## 11.3 Collision and mismatch handling

Reject:

```text
existing revision identifier with different digest
existing digest with incompatible canonical document
artifact digest mismatch
manifest digest mismatch
```

---

# 12. Phase 5 — Route and asset validation

## 12.1 Route-path safety

Reject:

```text
empty paths
relative paths
backslash paths
NUL bytes
dot segments
parent traversal
duplicate normalized paths
ambiguous percent encoding
encoded traversal
control characters
query strings in route declarations
fragments in route declarations
```

Normalize URL paths deterministically.

## 12.2 Artifact-path safety

Reuse V2-00 artifact-path guarantees.

Artifact paths must:

```text
be relative canonical artifact paths
exist in the immutable artifact manifest
not reference directories
not escape the artifact root
not resolve through symlinks
not use host filesystem paths
```

## 12.3 Route conflicts

Reject:

```text
duplicate exact routes
conflicting route ownership
ambiguous mount precedence
route shadowing unless explicitly defined
entry route not present
route to undeclared binding
route to undeclared file
```

## 12.4 Media types

Use the artifact manifest media type where available.

Do not infer executable server behavior from file extensions.

Allow only reviewed static response media types.

Server-side executable media types or handler mappings must not exist.

---

# 13. Phase 6 — Capsule host service boundary

## 13.1 Internal service

Add an internal capsule-host service boundary.

Suggested operations:

```text
list_capsules()
describe_capsule(capsule_id)
describe_capsule_revision(capsule_id, revision)
author_capsule(authoring_manifest)
open_host_session(request)
get_host_session(session_id)
close_host_session(session_id)
verify_capsule_revision(capsule_id, revision)
```

The service must own orchestration across:

```text
capsule portfolio
artifact store
route resolver
host policy
session manager
loopback HTTP adapter
evidence generation
```

## 13.2 Dependency direction

Expected direction:

```text
Python client
    ↓
capsule-host service boundary
    ↓
capsule package
    ↓
artifact-store read boundary
```

Prohibit:

```text
client importing internal route handlers
client directly opening artifact-store paths
capsule package importing CLI code
capsule host mutating builder internals
HTTP adapter owning canonical validation
```

## 13.3 Error normalization

Normalize errors such as:

```text
capsule_not_found
capsule_revision_not_found
artifact_not_found
artifact_integrity_failed
route_not_found
invalid_route
invalid_host_policy
session_not_found
session_expired
session_budget_exhausted
host_bind_failed
```

Do not expose raw filesystem paths, tracebacks, or internal socket details in normal client results.

---

# 14. Phase 7 — Host-session lifecycle

## 14.1 Session states

Use a bounded lifecycle such as:

```text
opening
active
closing
closed
failed
expired
```

Transitions must be explicit and tested.

## 14.2 Opening a session

Before binding:

```text
resolve capsule revision
verify capsule digest
verify every artifact digest
validate host policy
construct immutable route table
select loopback address
select bounded port
allocate session budget
```

Do not bind until all validation succeeds.

## 14.3 Active session

An active session must be:

```text
read-only
loopback-only
bounded by duration
bounded by request count
bounded by response size
restricted to declared methods
restricted to declared routes
```

## 14.4 Closing a session

Closing must:

```text
stop accepting requests
finish or cancel bounded in-flight work
release the socket
mark the session closed
record final metrics
emit evidence
remove temporary session resources
```

Closing an already closed session should be deterministic and safe.

## 14.5 Expiration

Sessions must close automatically after:

```text
maximum session duration
idle timeout
request-budget exhaustion
fatal integrity failure
```

The implementation must not require a durable scheduler.

An in-process bounded session manager is sufficient for V2-01.

---

# 15. Phase 8 — Loopback HTTP adapter

## 15.1 Binding

Bind only to:

```text
127.0.0.1
::1 where explicitly supported and tested
```

Do not bind to:

```text
0.0.0.0
::
external interfaces
user-provided hostnames
```

## 15.2 Methods

Initially support:

```text
GET
HEAD
```

Reject:

```text
POST
PUT
PATCH
DELETE
CONNECT
TRACE
OPTIONS unless required by a fixed reviewed policy
```

Request bodies must not be accepted.

## 15.3 Routing

For every request:

```text
normalize request path
reject malformed encodings
resolve exact declared route
verify binding
retrieve declared artifact file
enforce response limit
return reviewed headers
record bounded evidence
```

Do not expose directory listing or automatic filesystem traversal.

## 15.4 Security headers

Add a fixed reviewed baseline, such as:

```text
X-Content-Type-Options: nosniff
Referrer-Policy: no-referrer
Cache-Control appropriate to immutable local artifacts
Content-Security-Policy using a bounded reviewed value
```

Do not permit capsule-authored arbitrary response headers in V2-01.

## 15.5 Error responses

Return bounded non-sensitive responses for:

```text
400 malformed path
404 undeclared route
405 unsupported method
413 response exceeds policy
429 request budget exhausted
500 verified internal failure
503 session unavailable
```

Do not expose:

```text
stack traces
absolute paths
artifact-store locations
temporary directories
environment variables
```

---

# 16. Phase 9 — Evidence and effects

## 16.1 Authoring evidence

Record evidence for:

```text
capsule definition resolved
artifacts resolved
artifact integrity verified
routes validated
policy validated
revision digest calculated
revision published
```

## 16.2 Host evidence

Record bounded evidence for:

```text
session opened
loopback address selected
capsule digest verified
artifacts verified
route table created
requests served
requests rejected
budget exhausted
session closed
```

## 16.3 Effects

Opening and closing a session are temporary local effects.

Use existing effect-receipt conventions where appropriate.

Effect records must not imply production deployment.

## 16.4 Sensitive information

Evidence must exclude:

```text
raw file contents
credentials
environment variables
absolute host paths
full stack traces
unbounded request logs
user-agent fingerprints unless explicitly necessary
```

---

# 17. Phase 10 — Python client and CLI

## 17.1 Python client

Add bounded methods such as:

```text
list_capsules()
describe_capsule(capsule_id)
describe_capsule_revision(capsule_id, revision)
author_capsule(manifest)
verify_capsule(capsule_id, revision)
open_capsule(capsule_id, revision)
get_capsule_session(session_id)
close_capsule_session(session_id)
```

The client must delegate to the service boundary.

It must not directly access:

```text
capsule portfolio files
artifact-store directories
socket handlers
internal route tables
```

## 17.2 CLI

Add bounded commands such as:

```text
servicefabric capsule list
servicefabric capsule describe <capsule-id>
servicefabric capsule revision describe <capsule-id> --revision <revision>
servicefabric capsule author --manifest <reviewed-manifest-ref>
servicefabric capsule verify <capsule-id> --revision <revision>
servicefabric capsule open <capsule-id> --revision <revision>
servicefabric capsule session describe <session-id>
servicefabric capsule session close <session-id>
```

Do not accept:

```text
arbitrary source directory
arbitrary artifact-store path
arbitrary host address
arbitrary shell command
arbitrary route handler
arbitrary environment variables
```

## 17.3 Machine-readable output

All commands must support deterministic JSON output.

Stable output should include:

```text
status
capsule ID
revision
capsule digest
session ID where applicable
loopback URL where applicable
warnings
errors
evidence summary
```

## 17.4 Process-lifetime limitation

If sessions are in-process, document clearly that:

```text
the serving process must remain active
sessions are not durable across process restarts
sessions are local development facilities
```

Do not simulate durability.

---

# 18. Phase 11 — Verification and architecture guardrails

## 18.1 Contract tests

Test:

```text
strict validation
unknown-field rejection
immutable artifact references
invalid routes
invalid mounts
invalid host policies
schema determinism
fixture round trips
```

## 18.2 Authoring tests

Test:

```text
valid capsule authoring
missing artifact rejection
artifact mismatch rejection
duplicate-route rejection
mount conflict rejection
deterministic revision digest
atomic publication
identical revision reuse
immutable revision conflict
```

## 18.3 Routing tests

Test:

```text
exact route resolution
entry route
asset route
undeclared route rejection
encoded traversal rejection
duplicate normalized route rejection
missing artifact file rejection
media-type enforcement
```

## 18.4 Host-session tests

Test:

```text
loopback-only binding
GET support
HEAD support
unsupported-method rejection
request-body rejection
request-budget exhaustion
response-size enforcement
idle expiration
maximum-duration expiration
clean shutdown
idempotent close
```

Where the managed test environment prohibits socket creation, keep:

```text
core routing and lifecycle tests in-process
one clearly isolated loopback integration test
```

The mandatory architecture logic must remain testable without external networking.

## 18.5 Client and CLI tests

Test:

```text
service-boundary delegation
machine-readable JSON
stable errors
no arbitrary path options
no arbitrary host options
no direct artifact access
```

## 18.6 Regression tests

Continue running:

```text
V1 runtime tests
V1 integration tests
V2-00 application tests
V2-00 builder tests
V2-00 artifact tests
V2-00 preview tests
contract tests
schema snapshots
dependency locks
architecture guardrails
```

## 18.7 Architecture guardrails

Add tests that reject:

```text
subprocess execution in capsule packages
os.system usage
shell=True
Dockerfile execution
remote URL fetching
0.0.0.0 binding
public host defaults
direct client artifact-store access
capsule mutation of artifacts
database migration additions
Compose changes
Nginx changes
Django migration changes
arbitrary route callbacks
server-side application execution
```

---

# 19. Required completion checks

Before completion, replace the planned V2-01 check with executable checks similar to:

```json
[
  {
    "name": "v2-01-contracts",
    "command": [
      "python3",
      "-m",
      "unittest",
      "packages/servicefabric_contracts/tests/test_capsules.py",
      "-v"
    ],
    "required": true
  },
  {
    "name": "v2-01-capsules",
    "command": [
      "python3",
      "-m",
      "unittest",
      "discover",
      "-s",
      "tests/capsules",
      "-v"
    ],
    "required": true
  },
  {
    "name": "v2-01-authoring",
    "command": [
      "python3",
      "-m",
      "unittest",
      "discover",
      "-s",
      "tests/authoring",
      "-v"
    ],
    "required": true
  },
  {
    "name": "v2-01-routing",
    "command": [
      "python3",
      "-m",
      "unittest",
      "discover",
      "-s",
      "tests/routing",
      "-v"
    ],
    "required": true
  },
  {
    "name": "v2-01-host",
    "command": [
      "python3",
      "-m",
      "unittest",
      "discover",
      "-s",
      "tests/capsule_host",
      "-v"
    ],
    "required": true
  },
  {
    "name": "v2-01-boundaries",
    "command": [
      "python3",
      "-m",
      "unittest",
      "tests/architecture/test_v2_01_capsule_boundaries.py",
      "-v"
    ],
    "required": true
  },
  {
    "name": "v2-00-regressions",
    "command": [
      "python3",
      "scripts/agent/verify.py",
      "--milestone",
      "v2-00",
      "--phase",
      "completion"
    ],
    "required": true
  },
  {
    "name": "schema-snapshots",
    "command": [
      "python3",
      "scripts/contracts/check_schema_snapshots.py"
    ],
    "required": true
  },
  {
    "name": "dependency-locks",
    "command": [
      "python3",
      "scripts/dependencies/check_python_locks.py"
    ],
    "required": true
  },
  {
    "name": "architecture-guardrails",
    "command": [
      "python3",
      "scripts/architecture/check_legacy_patterns.py"
    ],
    "required": true
  }
]
```

Adjust test locations to actual implementation paths.

Do not leave any `planned: true` checks at milestone completion.

---

# 20. Phase sequence and commits

Implement in this order.

## Phase 1 — `capsule-contracts`

Deliver:

```text
canonical capsule contracts
fixtures
JSON Schemas
schema exports
contract tests
```

Suggested commit:

```text
feat: add immutable capsule contracts
```

## Phase 2 — `capsule-portfolio`

Deliver:

```text
file-backed capsule resources
portfolio resolver
reviewed example capsule
```

Suggested commit:

```text
feat: add reviewed capsule portfolio
```

## Phase 3 — `authoring-model`

Deliver:

```text
authoring manifest validation
deterministic normalization
diagnostics
atomic immutable publication
```

Suggested commit:

```text
feat: add declarative capsule authoring
```

## Phase 4 — `capsule-identity`

Deliver:

```text
canonical revision digest
reproducibility tests
identity mismatch handling
```

Suggested commit:

```text
feat: add reproducible capsule identity
```

## Phase 5 — `asset-and-route-resolution`

Deliver:

```text
route normalization
artifact bindings
route-table construction
conflict detection
```

Suggested commit:

```text
feat: add bounded capsule route resolution
```

## Phase 6 — `host-boundary`

Deliver:

```text
capsule-host service boundary
artifact verification integration
canonical errors
```

Suggested commit:

```text
feat: add capsule host service boundary
```

## Phase 7 — `session-lifecycle`

Deliver:

```text
session manager
state transitions
budgets
expiration
clean shutdown
```

Suggested commit:

```text
feat: add bounded capsule host sessions
```

## Phase 8 — `loopback-hosting`

Deliver:

```text
loopback HTTP adapter
GET and HEAD
security headers
bounded response handling
```

Suggested commit:

```text
feat: add loopback capsule hosting
```

## Phase 9 — `client-and-cli`

Deliver:

```text
Python client methods
bounded CLI
machine-readable output
```

Suggested commit:

```text
feat: add capsule client and CLI
```

## Phase 10 — `cross-boundary-verification`

Deliver:

```text
architecture guardrails
cross-boundary tests
regression checks
completion configuration
status update
handoff
```

Suggested commits:

```text
test: verify V2-01 integration boundaries
docs: complete V2-01 milestone status
```

---

# 21. Acceptance criteria

V2-01 is complete only when all of the following are true.

## Contracts

```text
capsule contracts are strict
schemas are deterministic
immutable references are enforced
unknown fields are rejected
invalid fixtures are covered
```

## Authoring

```text
authoring is declarative
authoring executes no commands
authoring performs no network access
equivalent inputs produce identical capsule digests
publication is atomic
published revisions are immutable
```

## Artifact integrity

```text
every artifact is referenced by digest
every artifact is verified before hosting
capsules cannot mutate artifacts
capsules cannot bypass artifact-store boundaries
```

## Routing

```text
routes are explicit
routes are deterministic
undeclared routes are unavailable
traversal is rejected
route conflicts are rejected
only declared artifact files are served
```

## Hosting

```text
host binds only to loopback
host supports only reviewed methods
host is read-only
host enforces request and response budgets
host sessions expire
host shuts down cleanly
host exposes no directory listing
host exposes no arbitrary filesystem path
```

## Architecture

```text
no shell execution
no arbitrary subprocess execution
no Dockerfile execution
no remote source retrieval
no dynamic backend execution
no production deployment
no persistent database registry
no Compose changes
no Nginx changes
no Django migrations
```

## Verification

```text
all V2-01 checks pass
all V2-00 completion checks pass
schema snapshots pass
dependency locks pass
architecture guardrails pass
compileall passes
git diff --check passes
make verify-current passes
make agent-handoff passes
working tree is clean
```

---

# 22. Known limitations to preserve

The completed implementation must explicitly report these limitations:

```text
static capsules only
immutable static-web artifacts only
local loopback hosting only
in-process non-durable sessions
no production availability guarantee
no authentication platform
no persistent registry
no database
no dynamic backend support
no remote source retrieval
no collaborative authoring
no browser authoring UI
no deployment orchestration
no distributed hosting
```

Do not disguise these limitations with placeholder abstractions that imply unsupported functionality.

---

# 23. Rollback

Rollback consists of reverting the V2-01 commits.

No rollback should require:

```text
database migration reversal
production deployment changes
container teardown
Nginx reconfiguration
DNS changes
TLS changes
remote artifact deletion
durable queue cleanup
```

Temporary local host sessions must terminate when their process exits.

No generated host-session state should be committed to the repository.

---

# 24. Completion report

At completion, report:

```text
Blockers
Changed areas
Validation
Reproducibility results
Security and architecture guardrails
Deviations
Known limitations
Rollback
Next-session prompt
```

The report must include:

```text
contract test count
capsule test count
authoring test count
routing test count
host-session test count
architecture test count
V2-00 regression result
schema snapshot result
dependency-lock result
make verify-current result
make agent-handoff result
```

---

# 25. Handoff to V3-00

After V2-01 merges:

```text
V2-01 becomes completed
V3-00 becomes current
```

V3-00 will own governance and durable operations.

V2-01 must not pre-implement:

```text
persistent operation registry
approval workflows
durable host operations
production deployment approvals
multi-user governance
audit database
distributed workers
```

Before merge, generate the repository-native handoff and confirm that no V3-00 implementation is present on the V2-01 branch.
