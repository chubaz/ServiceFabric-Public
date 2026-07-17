# Engineering blueprint

## Factory run topology

One `AgentRunPlan` represents one bounded factory run for an immutable `ApplicationIntent`. The blueprint compiler emits a task DAG: foundation and feature lanes have disjoint `allowed_paths`; each declares dependencies, expected outputs, and verification commands. An assurance lane reports verification evidence. The application-integration lane depends on every candidate selected for the application and alone owns shared application paths, conflict resolution, full verification, and closure.

Candidate work uses one branch and worktree per executable task, created from the approved integration base. Candidate worktrees do not merge one another. Candidate results are reviewed before the integration authority selects commits or rejects/reworks the result.

## Authority rules

- A task result is candidate evidence, not acceptance.
- Dependency IDs express ordering; they do not grant cross-lane path ownership.
- Optional `commit_sha` never grants merge authority by itself.
- Only application integration may reconcile shared files, dependency versions, application-wide verification, or final handoff status.
- Unknown, timeout, blocked, cancelled, result-less, or failed provider results are not dependency inputs without an explicit review decision.

## Decisions reserved for a later implementation wave

Path matching and overlap rules; worktree creation and cleanup; base/rebase policy; prompt and context assembly; evidence sufficiency; retry and rollback policy; provider fallback and scheduling; human approval; and application success semantics require approved design decisions before implementation.

## Wave-8-dependent assumptions

**Wave-8-dependent assumption:** the provider runtime and adapters can execute a bounded request in an isolated repository, collect ordered events and usage, create diagnostic artifacts, recover a canonical result, and enforce provider policy. These are interfaces in the Wave-8 contracts, not evidence of completed operational behavior. Wave-9 execution design remains blocked until Wave-8 closure confirms them.
