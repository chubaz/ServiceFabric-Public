Review and correct the current ServiceFabric application-platform milestone.

Do not begin the next milestone.

## Review objective

Determine whether the current branch delivers a real vertical user journey rather than only models, adapters and isolated tests.

Read:

```text
current milestone workplan
actual branch diff
all new application examples
CLI entry point
composition root
hosting code
gateway routing
resource observation
acceptance tests
programme status
```

## Required review

### 1. Fresh user journey

From a clean temporary workspace and clean installation, run the milestone’s complete documented CLI journey.

Do not substitute direct Python calls for installed commands.

Verify:

```text
install or create
build
start
health
status
resource view
capability discovery
capability invocation
operation following where applicable
stop
unavailable behaviour after stop
```

### 2. Real boundaries

Confirm that:

```text
CLI does not call application actions directly
frontend does not manipulate hosting state directly
gateway remains the capability entry point
governance is not bypassed
application and capability identities remain separate
application availability controls capability availability
resource values come from real observation where labelled observed
```

### 3. No mock-only completion

Identify any principal acceptance claim that only works with:

```text
fake application
fake gateway
fake process host
fake resource readings
in-process-only test fixture
hard-coded successful result
```

Replace it with a real local end-to-end path where required.

### 4. Lifecycle failures

Exercise:

```text
build failure
start failure
health failure
unexpected process exit
stopped application call
invalid input
unknown capability
resource observer failure
operation failure or cancellation where present
```

Errors must be understandable and safe.

### 5. Resource honesty

Verify that declared estimates and observed values are not mixed.

Check that process and module measurements correspond to the actual hosted process tree.

### 6. Security and containment

Confirm:

```text
loopback-only default
no unrestricted shell execution
reviewed commands or framework adapters only
no literal secrets in records
no automatic exposure of all application actions
no use of the legacy dynamic Flask tool path
no dangerous Codex-generated development shortcut left in production code
```

### 7. Regression and cleanliness

Run:

```text
all prior milestone completion gates
current milestone completion gate
V1–V4 regressions
schema determinism where applicable
dependency checks
architecture checks
compile/type checks
frontend builds
CLI subprocess tests
browser tests where applicable
git diff --check
working-tree check
```

## Corrections

Fix all blocking and high-impact findings on the same branch.

Use focused corrective commits.

Do not rewrite good commit history merely for style.

Do not open or merge the pull request.

## Final report

Report:

```text
reviewed head
findings by severity
correction commits
fresh-install journey
actual commands executed
actual application processes used
actual resource measurements
capability route
negative journeys
exact test counts
remaining limitations
working-tree status
PR readiness: ready or not ready
```
