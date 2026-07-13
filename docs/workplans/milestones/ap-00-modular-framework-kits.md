# AP-00: Modular Framework Kits

## Objective
Define reusable, reviewed framework kits from AP-01A evidence without making framework internals part of canonical application identity.

## Starting conditions
AP-01A is merged and its Text Utility journey remains a passing regression.

## Scope
Specify bounded adapters, package templates, validation, and conformance tests for supported frameworks. Preserve application/package/tool separation and explicit reviewed start behavior.

## Exclusions
No resource-aware scheduling, application capability connections, public hosting, unrestricted commands, or legacy runtime migration.

## Acceptance and rollback
Framework kits reproduce the AP-01A journey without weakening its architecture tests. Revert the milestone commits; no persistent-data migration is expected.
