# Wave-9 objective: Autonomous Application Factory

Wave-9 implements an Autonomous Application Factory for a bounded `ApplicationIntent`. A factory run selects and approves an `ApplicationBlueprint` and reviewed technology profile, compiles an `EngineeringBlueprint`, bootstraps a named application repository and integration branch, executes isolated lane candidates, reviews them, integrates accepted commits, validates the application, and returns a final handoff or structured unmet requirements.

The factory reuses the canonical `ApplicationIntent`, `AgentTask`, `AgentRunPlan`, `ProviderPolicy`, `ProviderExecutionService`, `ApplicationBlueprint`, `ApplicationGenerator`, `FrameworkKitCatalog`, `AgenticApplicationService`, `FileRunStore`, bounded verification, and `CapabilityConsumerFacade`. It does not create a second generator, provider runtime, scheduler, kit catalogue, capability registry, or generic run store.

## Outcomes

1. Reviewed blueprint and technology-profile approvals.
2. An engineering lane DAG with bounded parallelism.
3. Repository, integration branch, and one candidate branch/worktree per lane from an exact approved base.
4. Candidate-review decisions before integration.
5. Accepted-commit-only integration, declared verification, and a final factory handoff.
6. Structured unmet requirements scoped to application, library, framework-kit, primitive, or platform.

## Wave-8 foundation

Wave-8 provider execution is a completed dependency. Wave-9 uses its canonical policy, execution, recovery, event, usage, and result contracts through `ProviderExecutionService`; the factory owns approvals, candidate review, integration, and handoff state only.

## Exclusions

The factory never installs dependencies while selecting technology, duplicates a provider runtime or task scheduler, trusts remote inventory automatically, force-resets, force-pushes, deletes application state, or merges into `main` automatically.
