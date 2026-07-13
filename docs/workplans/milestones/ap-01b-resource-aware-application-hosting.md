# AP-01B: Resource-Aware Application Hosting

## Objective
Extend bounded hosting with resource-aware admission and recovery based on measurements established by AP-01A.

## Starting conditions
AP-01A and AP-00 are merged and their installed-CLI journeys pass.

## Scope
Define explicit resource policies, admission decisions, bounded restart behavior, and observable lifecycle diagnostics while preserving immutable package identity.

## Exclusions
No distributed scheduler, Kubernetes, public hosting, billing, or AP-02 connection model.

## Acceptance and rollback
Tests distinguish declarations, estimates, measurements, and policy decisions. Revert commits and remove local test state; no production cleanup is required.
