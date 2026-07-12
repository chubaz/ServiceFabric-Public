# V2-00 — Immutable Application Builder

## 1. Objective

Implement the first bounded ServiceFabric application-building vertical slice.

V2-00 must allow ServiceFabric to accept a reviewed application definition, validate and normalize its inputs, execute a deterministic static-web build through an isolated build adapter, produce an immutable content-addressed artifact, and expose that artifact through a bounded local preview boundary.

The initial vertical slice is:

```text
reviewed application definition
        ↓
validated source bundle
        ↓
deterministic static-web build
        ↓
immutable content-addressed artifact
        ↓
artifact manifest and provenance
        ↓
bounded local preview
```

V2-00 is an application builder, not a general-purpose CI system, deployment platform, container service, or arbitrary code execution facility.

---

# 2. Starting conditions

Start from the merged V1-01 milestone.

Required baseline:

```text
E0-00 completed
V1-00 completed
V1-01 completed
V2-00 current
working tree clean
canonical specification hashes valid
V1-01 completion verification passing
```

Before editing, run:

```bash
make agent-preflight
make agent-context
make verify-current
```

At the beginning of V2-00, `make verify-current` may run readiness checks while V2-00 completion checks remain marked as planned.

Before merging V2-00:

```text
all planned completion checks must be replaced
all completion commands must be executable
all required checks must pass
handoff to V2-01 must be generated
```

---

# 3. Governing principles

## 3.1 Immutable outputs

A successful build produces an immutable artifact identified by its content.

The artifact identity must not depend on:

```text
build timestamp
temporary directory
machine hostname
process identifier
random identifier
absolute workspace path
log ordering
```

Where inputs are equivalent and the build is declared reproducible, repeated builds must produce the same artifact digest.

## 3.2 Reviewed application definitions

ServiceFabric must build only applications represented by reviewed canonical definitions.

The builder must not accept arbitrary:

```text
shell commands
Dockerfiles
package-manager scripts
build pipelines
remote repositories
unbounded file trees
environment variable injection
host filesystem paths
```

## 3.3 Separation of definition, build and hosting

Keep these concepts distinct:

```text
ApplicationDefinition
    what the application is

ApplicationRevision
    immutable reviewed source and build specification

ApplicationBuildRequest
    request to build one reviewed revision

ApplicationArtifact
    immutable build output

PreviewSession
    bounded temporary presentation of an artifact
```

Do not collapse these into one mutable application object.

## 3.4 Build adapters

The canonical builder owns:

```text
validation
source normalization
build identity
artifact identity
provenance
budgets
timeouts
result normalization
```

A build adapter owns only execution for one approved build type.

## 3.5 No general-purpose command execution

The initial implementation must use a fixed native static-site build adapter.

It must not implement:

```text
exec(command)
run_shell(script)
custom build command
user-provided command arrays
arbitrary subprocess launch
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

packages/servicefabric_contracts/
packages/servicefabric_runtime/
services/tool_runtime/
clients/python/
```

Read the V1-00 and V1-01 workplans for existing conventions around:

```text
canonical contracts
immutable revisions
portfolio resources
execution boundaries
evidence
effects
agent verification
```

Do not change canonical architectural decisions unless a real conflict is found and documented through an ADR.

---

# 5. Scope

V2-00 includes:

```text
application definition contracts
application revision contracts
build request and result contracts
artifact manifest contracts
file-backed application portfolio
bounded source-bundle validation
native static-web build adapter
content-addressed artifact storage
build provenance
deterministic build verification
Python client support
CLI support
bounded local artifact preview
tests and architecture guardrails
```

V2-00 excludes:

```text
dynamic backend applications
database-backed applications
user-authored Dockerfiles
arbitrary build systems
Node, npm or frontend framework execution
remote Git cloning
production hosting
public deployment
domain management
TLS management
load balancing
durable job queues
distributed workers
persistent database registry
authoring UI
capsule authoring
MCP application projection
automatic tool generation from applications
workstation mutation
```

---

# 6. Initial supported application type

V2-00 supports exactly one application type:

```text
static_web
```

A `static_web` application consists of a bounded set of reviewed files such as:

```text
index.html
CSS files
JavaScript files
images
fonts owned or licensed by the application author
other static assets explicitly permitted by policy
```

The initial builder may copy, normalize and package reviewed static files.

It must not execute JavaScript, TypeScript, CSS preprocessors or package-manager commands during the build.

The build is therefore a deterministic static asset assembly process, not a frontend compilation pipeline.

---

# 7. Expected implementation areas

Follow repository conventions established by prior milestones.

Expected additions may include:

```text
packages/
├── servicefabric_contracts/
│   └── application and artifact contracts
├── servicefabric_builder/
│   └── canonical builder implementation
└── servicefabric_artifacts/
    └── artifact storage and verification

services/
└── application_builder/
    └── internal service boundary

clients/
└── python/
    └── application build and artifact operations

portfolio/
├── applications/
│   ├── definitions/
│   └── revisions/
└── examples/

tests/
├── builder/
├── artifacts/
├── applications/
├── preview/
└── architecture/
```

Use different paths where existing repository conventions clearly require them.

Do not reorganize V1-00 or V1-01 code merely to match this conceptual layout.

---

# 8. Phase 1 — Application contracts

## 8.1 ApplicationDefinition

Add a canonical `ApplicationDefinition`.

It should describe stable application identity and metadata.

Suggested fields:

```text
api_version
kind
application_id
display_name
description
application_type
status
labels
annotations
```

Constraints:

```text
application_id must be stable and validated
application_type must initially equal static_web
unknown fields must be rejected where canonical contracts require strictness
definitions must not contain raw source contents
definitions must not contain credentials
```

## 8.2 ApplicationRevision

Add an immutable `ApplicationRevision`.

Suggested fields:

```text
api_version
kind
application_id
revision
application_type
source_bundle_ref
source_digest
build_spec
output_spec
created_from
status
```

The revision must identify immutable reviewed source content.

The revision must not reference:

```text
mutable branch names
latest tags
unversioned remote URLs
host filesystem paths
temporary files
```

## 8.3 StaticWebBuildSpec

Add a bounded build specification.

Suggested shape:

```text
entry_document
include_patterns
exclude_patterns
maximum_file_count
maximum_source_bytes
maximum_output_bytes
normalization_policy
```

Do not permit:

```text
custom command
pre_build command
post_build command
environment variable map
runtime image
Dockerfile
package manager
```

## 8.4 SourceBundleManifest

Define a source bundle manifest containing:

```text
path
content_digest
media_type
size_bytes
executable
```

For V2-00:

```text
executable must always be false
symlinks must be rejected
device files must be rejected
absolute paths must be rejected
parent traversal must be rejected
```

## 8.5 ApplicationBuildRequest

Define a canonical request containing:

```text
application_id
revision
requested_artifact_format
build_options
caller_context
execution_budget
correlation metadata
```

Only reviewed options may be accepted.

## 8.6 ApplicationBuildResult

Define a canonical result containing:

```text
status
application_id
revision
build_id
artifact_ref
artifact_digest
artifact_manifest_ref
warnings
errors
evidence
metrics
```

Use existing canonical result and error conventions where possible.

Do not create an incompatible parallel error system.

## 8.7 ApplicationArtifactManifest

Define an immutable artifact manifest containing:

```text
artifact_id
artifact_digest
application_id
application_revision
builder_id
builder_revision
source_digest
build_spec_digest
files
entry_document
total_size_bytes
created_at
reproducibility
provenance
```

`created_at` may exist as metadata but must not influence `artifact_digest`.

---

# 9. Phase 2 — Application portfolio

## 9.1 File-backed resources

Add file-backed portfolio locations for:

```text
application definitions
application revisions
source bundle manifests
```

Use the existing portfolio resolver conventions where possible.

Do not introduce a database registry.

## 9.2 Example application

Add one reviewed example:

```text
examples.hello-static
```

or another identifier consistent with repository conventions.

It should contain:

```text
index.html
one stylesheet
one bounded JavaScript file or no JavaScript
one small image or static asset where useful
```

The example must not require network access or external CDNs.

## 9.3 Resolution

The portfolio resolver must:

```text
resolve definition by ID
resolve immutable revision
resolve source bundle manifest
verify source digest
reject missing files
reject undeclared files where strict mode applies
```

---

# 10. Phase 3 — Source validation and normalization

## 10.1 Path safety

Reject:

```text
absolute paths
../ traversal
empty paths
duplicate normalized paths
Windows drive prefixes
UNC paths
NUL bytes
symlinks
hard-link metadata
device files
named pipes
sockets
```

Normalize path separators deterministically.

## 10.2 File limits

Enforce bounded:

```text
file count
individual file size
total source size
path length
path segment length
manifest size
```

Limits must be configured by trusted builder policy, not application-authored arbitrary values.

## 10.3 Media types

Allow a reviewed bounded set such as:

```text
text/html
text/css
application/javascript
application/json
image/png
image/jpeg
image/svg+xml
image/webp
image/x-icon
font/woff
font/woff2
text/plain
```

Reject executable and server-side file types.

SVG handling must be explicitly reviewed because SVG may contain scripts or external references.

The simplest safe V2-00 choice is either:

```text
reject SVG
```

or:

```text
allow only sanitized reviewed SVG fixtures
```

Do not silently trust declared media type.

## 10.4 Text normalization

Where enabled, normalize reviewed text files deterministically:

```text
UTF-8
LF line endings
no UTF-8 BOM
stable final newline policy
```

Do not modify binary files.

## 10.5 Stable ordering

All manifest entries and artifact entries must use a deterministic order, such as normalized path order.

---

# 11. Phase 4 — Static-web build adapter

## 11.1 Package

Create a builder package such as:

```text
packages/servicefabric_builder/
```

Suggested modules:

```text
models.py
source.py
normalization.py
identity.py
builder.py
static_web.py
errors.py
testing.py
```

## 11.2 Adapter interface

Define a narrow interface such as:

```python
class ApplicationBuildAdapter(Protocol):
    def build(
        self,
        revision: ApplicationRevision,
        source: ValidatedSourceBundle,
        budget: BuildBudget,
    ) -> BuildOutput:
        ...
```

The exact API should match repository style.

## 11.3 Native static builder

The initial adapter must:

```text
validate source files
normalize approved text files
copy approved files into an isolated temporary output directory
verify the entry document exists
generate the artifact manifest
calculate stable file digests
calculate artifact digest
return normalized build output
```

It must not:

```text
invoke a shell
execute source code
contact the network
load arbitrary plugins
resolve remote dependencies
write outside its workspace
```

## 11.4 Temporary workspace

Use a fresh temporary directory outside the repository working tree.

Requirements:

```text
workspace path is builder controlled
source extraction remains inside workspace
output remains inside workspace
workspace is removed after success or failure
workspace path never affects artifact identity
```

## 11.5 Build budgets

Add bounded controls for:

```text
maximum source bytes
maximum output bytes
maximum files
maximum elapsed time
maximum manifest size
```

A native static copy build should normally complete synchronously.

Use existing execution-budget concepts where compatible.

---

# 12. Phase 5 — Build identity and reproducibility

## 12.1 Build input identity

Compute a stable build-input digest from canonical representations of:

```text
application ID
application revision
source digest
normalized build specification
builder ID
builder revision
reproducibility policy
```

Do not include:

```text
timestamp
temporary directory
hostname
user name
process ID
random ID
```

## 12.2 Artifact identity

Compute the artifact digest from canonical artifact contents and stable manifest fields.

A recommended approach is:

```text
sort files by normalized path
for each file include:
    normalized path
    content digest
    size
    media type
include stable artifact metadata
serialize canonically
hash canonical representation
```

## 12.3 Reproducibility classification

Record one of:

```text
reproducible
conditionally_reproducible
not_reproducible
```

The initial static-web builder should be `reproducible`.

## 12.4 Rebuild verification

Provide an operation or test helper that builds the same revision twice and confirms:

```text
artifact digest identical
manifest semantic content identical
file digests identical
```

Timestamps and temporary references may differ but must be excluded from digest-bearing content.

---

# 13. Phase 6 — Artifact storage

## 13.1 Storage interface

Create a narrow artifact store interface.

Suggested operations:

```text
put_artifact
get_manifest
open_file
has_artifact
verify_artifact
```

Do not implement:

```text
mutable overwrite
artifact update
artifact patch
latest artifact alias with mutable semantics
```

## 13.2 File-backed store

Implement a local file-backed store for V2-00.

Suggested layout:

```text
.artifacts/
└── sha256/
    └── ab/
        └── <full-digest>/
            ├── manifest.json
            └── files/
```

Prefer a configurable path outside the Git repository.

Tests must use temporary directories.

Do not commit generated artifact contents.

## 13.3 Atomic publication

Publish artifacts atomically:

```text
write to temporary artifact directory
verify manifest and file digests
rename into final digest path
```

If the artifact already exists:

```text
verify existing content
reuse it if identical
raise integrity error if inconsistent
```

## 13.4 Read-only semantics

Once published, artifact files must be treated as immutable.

The API must not expose arbitrary filesystem paths.

---

# 14. Phase 7 — Artifact verification

Implement verification that:

```text
loads the manifest
verifies artifact digest
verifies every declared file exists
verifies no undeclared file exists
verifies every file digest
verifies total size
verifies entry document
```

Return a structured verification result.

Do not return only a boolean.

Suggested result fields:

```text
valid
artifact_digest
verified_files
missing_files
unexpected_files
digest_mismatches
warnings
errors
```

---

# 15. Phase 8 — Application builder service boundary

## 15.1 Internal service

Create an internal boundary such as:

```text
services/application_builder/
```

Suggested operations:

```text
build_application
get_artifact_manifest
verify_artifact
open_artifact_file
```

A network transport is not required for V2-00.

The service may initially be an in-process service boundary consistent with V1-00.

## 15.2 Canonical execution path

The intended path is:

```text
Python client or CLI
    → application builder service
    → canonical builder
    → static-web adapter
    → artifact store
```

Clients must not invoke adapter internals directly.

---

# 16. Phase 9 — Python client and CLI

## 16.1 Python client

Extend the existing Python client with operations similar to:

```python
client.build_application(
    application_id="examples.hello-static",
    revision="1.0.0",
)

client.get_artifact_manifest(artifact_digest)

client.verify_artifact(artifact_digest)
```

Use repository naming conventions.

## 16.2 CLI

Add bounded CLI operations such as:

```text
servicefabric app list
servicefabric app describe <application-id>
servicefabric app build <application-id> --revision <revision>
servicefabric artifact describe <digest>
servicefabric artifact verify <digest>
servicefabric artifact preview <digest>
```

Requirements:

```text
machine-readable JSON mode
stable exit codes
no arbitrary source directory argument
no arbitrary output directory argument
no custom command option
no environment injection
```

---

# 17. Phase 10 — Bounded local preview

## 17.1 Purpose

Allow a user to inspect an already-built immutable static artifact locally.

Preview is not production hosting.

## 17.2 Preview behavior

The preview boundary may:

```text
serve artifact files read-only
bind to loopback only by default
select a bounded port
set safe content types
serve the declared entry document
reject path traversal
disable directory listing
disable upload and mutation
```

## 17.3 Security headers

Where practical, set:

```text
X-Content-Type-Options: nosniff
Referrer-Policy
Content-Security-Policy suitable for the sample artifact
Cache-Control appropriate for immutable files
```

Do not claim the preview server is production hardened.

## 17.4 Lifecycle

Preview should be:

```text
explicitly started
bounded to one artifact
read-only
cancellable
terminated cleanly
```

Do not implement a persistent daemon unless the repository already has a safe bounded pattern.

## 17.5 Testability

Tests must not require a long-running interactive process.

Use an in-process server fixture or request handler tests.

---

# 18. Evidence, effects and audit

## 18.1 Build evidence

A successful build should produce evidence references for:

```text
source manifest
source digest
build specification
builder revision
artifact manifest
artifact digest
verification result
```

Use existing evidence contracts where possible.

## 18.2 Effects

Building and storing an artifact is a controlled filesystem effect.

Represent it consistently with existing effect concepts if applicable.

Do not invent production-grade approval workflows in V2-00.

## 18.3 Logs

Logs must not contain:

```text
raw source contents
credentials
absolute user home paths
temporary directory internals where avoidable
unbounded binary data
```

Build logs should contain stable high-level events:

```text
validation started
source validated
build started
artifact calculated
artifact published
artifact verified
```

---

# 19. Error model

Use stable structured errors.

Suggested categories:

```text
application_not_found
application_revision_not_found
invalid_application_definition
invalid_source_bundle
unsafe_source_path
unsupported_media_type
source_limit_exceeded
output_limit_exceeded
entry_document_missing
build_timeout
artifact_integrity_error
artifact_not_found
artifact_verification_failed
preview_error
internal_builder_error
```

Do not expose raw stack traces through client or CLI output.

---

# 20. Testing strategy

## 20.1 Contract tests

Cover:

```text
valid application definition
invalid application ID
unsupported application type
immutable revision validation
invalid source references
build specification restrictions
artifact manifest validation
build result validation
strict unknown-field behavior
schema export
```

## 20.2 Source validation tests

Cover:

```text
valid bounded source
absolute path rejection
parent traversal rejection
duplicate normalized path rejection
symlink rejection
file-count limit
individual-size limit
total-size limit
unsupported media type
invalid UTF-8
stable text normalization
stable path ordering
```

## 20.3 Builder tests

Cover:

```text
successful static build
entry document validation
stable output ordering
no shell execution
no network execution
workspace cleanup
timeout behavior
source limit failure
output limit failure
safe error normalization
```

## 20.4 Reproducibility tests

Build the same source twice in different temporary directories.

Assert:

```text
same source digest
same build-input digest
same artifact digest
same stable manifest content
same file digests
```

Also verify that changing one byte changes the artifact digest.

## 20.5 Artifact store tests

Cover:

```text
atomic publication
deduplicated identical artifact
integrity mismatch detection
manifest retrieval
file retrieval
missing file
unexpected file
digest mismatch
read-only semantics
```

## 20.6 Client tests

Cover:

```text
application listing
application description
build request construction
successful result mapping
artifact retrieval
artifact verification
safe errors
```

## 20.7 CLI tests

Cover:

```text
bounded commands
JSON output
successful build
invalid application
artifact verification
safe exit codes
no arbitrary command options
```

## 20.8 Preview tests

Cover:

```text
serves entry document
serves declared asset
rejects traversal
rejects undeclared file
no directory listing
correct content type
read-only methods only
loopback default
clean shutdown
```

## 20.9 Architecture tests

Verify:

```text
contracts import no builder implementation
builder core imports no preview server implementation
client imports no adapter internals
static builder invokes no shell
static builder performs no network access
artifact store does not expose arbitrary filesystem paths
no Dockerfile execution support exists
no arbitrary build command field exists
no Compose files changed
no Django migrations added
no legacy catalogue or templates modified
```

---

# 21. Dependency management

Prefer the Python standard library where reasonable.

New dependencies must be:

```text
minimal
package-local
locked
justified
not added to unrelated runtimes
```

Do not add frontend build tools.

Do not require:

```text
Node.js
npm
pnpm
yarn
Docker
Podman
external object storage
database servers
```

for V2-00 tests.

---

# 22. Verification configuration

At the beginning of V2-00, completion checks may be planned.

Before merge, replace them with actual commands covering at least:

```text
contract tests
builder tests
source-validation tests
artifact tests
reproducibility tests
client tests
CLI tests
preview tests
architecture tests
schema snapshots
dependency-lock validation
agent tests
git diff check
```

Recommended logical checks:

```text
v2-00-contracts
v2-00-builder
v2-00-artifacts
v2-00-reproducibility
v2-00-client-cli
v2-00-preview
v2-00-boundaries
schema-snapshots
architecture-guardrails
dependency-locks
```

Use the actual discovery roots created by the implementation.

---

# 23. Suggested implementation phases

Track these phases in `docs/workplans/status.json`:

```text
application-contracts
application-portfolio
source-validation
static-web-builder
artifact-identity
artifact-storage
builder-service
client-and-cli
local-preview
cross-boundary-verification
```

Suggested sequence:

```text
1. application-contracts
2. application-portfolio
3. source-validation
4. static-web-builder
5. artifact-identity
6. artifact-storage
7. builder-service
8. client-and-cli
9. local-preview
10. cross-boundary-verification
```

---

# 24. Suggested commit sequence

Use logical commits such as:

```text
docs: define V2-00 immutable application builder
feat: add application and artifact contracts
feat: add reviewed static application portfolio
feat: validate and normalize static source bundles
feat: add deterministic static-web builder
feat: add content-addressed artifact identity
feat: add immutable file-backed artifact store
feat: add application builder service boundary
feat: add application client and CLI operations
feat: add bounded local artifact preview
test: verify V2-00 integration boundaries
docs: complete V2-00 milestone status
```

Do not combine the entire milestone into one commit.

---

# 25. Scope prohibitions

Do not:

```text
execute arbitrary shell commands
accept user-provided build commands
accept user-provided Dockerfiles
run package-manager lifecycle scripts
clone remote repositories
download dependencies
execute application JavaScript during build
add dynamic backend application support
add database application support
add production deployment
add domain or TLS management
add public hosting
add distributed queues
add persistent application registry
add Django models or migrations
modify Compose
modify Nginx
modify legacy templates
modify legacy catalogue loading
add application authoring UI
add capsule authoring
add generic plugin loading
store generated artifacts in Git
expose arbitrary host paths
```

---

# 26. Stop conditions

Stop and report if:

```text
canonical hashes differ
V1-01 is absent from main
V1-01 completion checks fail
application identity cannot be separated from build identity
artifact identity requires timestamps or mutable fields
the implementation requires arbitrary shell execution
the implementation requires Docker
the implementation requires Node or npm
the source bundle cannot be bounded safely
artifact publication cannot be atomic
preview requires public network binding
builder dependencies would leak into contract packages
a database is required
a production hosting platform is required
```

Do not bypass a stop condition through a permissive fallback.

---

# 27. Acceptance criteria

V2-00 is complete when:

```text
[ ] ApplicationDefinition exists and is schema exported.
[ ] ApplicationRevision exists and is immutable.
[ ] StaticWebBuildSpec rejects arbitrary commands.
[ ] SourceBundleManifest validates bounded reviewed files.
[ ] ApplicationBuildRequest and ApplicationBuildResult exist.
[ ] ApplicationArtifactManifest exists.
[ ] One reviewed static-web application is in the file-backed portfolio.
[ ] Unsafe paths and symlinks are rejected.
[ ] Source size and file-count limits are enforced.
[ ] Static build execution uses no shell and no network.
[ ] Equivalent builds produce the same artifact digest.
[ ] One-byte source changes produce a different artifact digest.
[ ] Artifact storage is content addressed.
[ ] Artifact publication is atomic.
[ ] Existing identical artifacts are reused safely.
[ ] Artifact verification checks every file and the manifest.
[ ] Python client can build and inspect an application.
[ ] CLI can build, inspect and verify an artifact.
[ ] Local preview serves one immutable artifact read-only.
[ ] Preview rejects traversal and mutation.
[ ] No generated artifacts are committed.
[ ] No Docker, Node or package manager is required.
[ ] No database registry is introduced.
[ ] No production deployment system is introduced.
[ ] All V2-00 completion checks are real and passing.
[ ] Handoff to V2-01 is generated.
```

---

# 28. Known limitations to retain

At V2-00 completion, explicitly retain:

```text
static applications only
no frontend compilation
no remote source retrieval
no dynamic backend
no production hosting
no distributed build execution
no durable build queue
no authoring UI
no capsule hosting
no deployment orchestration
local file-backed artifact storage only
```

---

# 29. Completion report

Report only:

## Starting state

```text
branch
base commit
V1-01 merge commit
working-tree state
```

## Changed areas

```text
contracts
application portfolio
source validation
builder
artifact identity
artifact storage
service boundary
client
CLI
preview
tests
agent configuration
```

## Build behavior

Explain concisely:

```text
how source bundles are validated
how build identity is calculated
how artifact identity is calculated
how reproducibility is verified
how artifacts are published atomically
how preview remains bounded
```

## Validation

Provide:

```text
test groups
test counts
verification status
schema status
lock status
architecture status
working-tree status
```

## Deviations

List deviations from this workplan.

## Known limitations

List the retained limitations above.

## Rollback

Normal PR revert.

Generated artifact stores created during testing may be deleted safely.

No persistent database migration should exist.

## Next milestone

```text
V2-01 — Capsule hosting and authoring
```

Stop after V2-00.

---

# 30. Handoff target

At V2-00 completion:

```text
e0-00 = completed
v1-00 = completed
v1-01 = completed
v2-00 = completed
v2-01 = current
```

Update:

```text
config/agent/milestones.json
docs/workplans/current.md
docs/workplans/status.json
```

Create a valid V2-01 milestone object and committed workplan placeholder before completing the handoff.

Do not implement V2-01 on the V2-00 branch.
