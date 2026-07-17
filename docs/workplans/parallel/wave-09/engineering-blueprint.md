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

`EngineeringLane` compiles to canonical `AgentTask` fields without duplicating them. Lanes must have disjoint candidate ownership; the integration lane alone owns shared-path reconciliation and the acceptance lane records application-level evidence. Repository bootstrap supplies the exact base branch/worktree and lane guidance, while provider execution remains delegated to Wave-8.
