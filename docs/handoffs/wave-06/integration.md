# Wave-6 Integration Handoff

## Projection Candidate Review

`contractsStatus: frozen` remains in force. Acceptance was not launched or reviewed.

### MCP projection — returned

Candidate head: `cf08735ce1d07560d34130ce623d025756599215`.

The three focused tests passed. The candidate was returned without merge because its commits use disallowed lane subjects (`feat(mcp):` and `docs(handoff):`), and the projection injects and calls `CapabilityRegistry` directly. This conflicts with the frozen boundary that projections delegate to `CapabilityRuntimeService` and do not own registry behavior.

### REST projection — returned

Candidate head: `1b847552921336c9b3d671d3bc91504dad01351a`.

The three focused loopback tests passed when executed outside the sandbox socket restriction; the server enforces literal `127.0.0.1` binding. The candidate was returned without merge because its required `list_capabilities` and `describe_capability` runtime operations are absent from the frozen concrete Wave-5 `CapabilityRuntimeService`. Adding them changes a frozen contract; reading the registry in the projection or an adapter violates the direct runtime-delegation boundary.

### Python and agent projection — accepted

Candidate head: `c62aa2bbe103f12c641d60cf818f5b2acaf8f172`; merged by `a530cf7d4fac4347e2dd520c14311c8ccbfad86c`.

The candidate changes only its owned package, tests, and handoff; its three focused tests pass before and after merge. `CapabilityClient` and the immutable internal-agent reference delegate directly to the frozen runtime availability, application-scoped discovery, and invocation APIs. No registry, endpoint, or invocation logic is introduced in consumers.

## Directly Dependent Verification

- MCP focused suite: passed, 3 tests.
- REST focused suite: passed, 3 tests on literal loopback.
- Python and agent focused suite: passed, 3 tests before and after merge.
- `git diff --check`: passed.

## Next Action

Return corrected MCP and REST candidates, then review composition. Acceptance remains blocked pending all three projections and integration composition.

## Rollback

Revert merge `a530cf7d4fac4347e2dd520c14311c8ccbfad86c` to remove the accepted Python and agent projection. No frozen contract changed.

## Projection Candidate Review #2

`contractsStatus: frozen` remains in force. Acceptance was neither launched nor reviewed.

### MCP projection — returned

Candidate head remains `cf08735ce1d07560d34130ce623d025756599215`; no corrected MCP candidate was supplied after the prior return. Its three focused tests pass, but the candidate still injects and calls `CapabilityRegistry` directly. That violates the projection boundary: consumers must delegate through the frozen `CapabilityRuntimeService` and do not own registry behavior. It was not merged.

### REST projection — returned

Candidate head: `c3690831e18eb9f3f27c9d5881cf68dfd9a43dfd`, including source-layout correction `b49369976bc0cfa89366581c72cdc91e770462da`. Its three focused loopback tests pass when run outside the managed sandbox's socket restriction, and the server continues to enforce literal `127.0.0.1` binding. The correction does not resolve the contract issue: the gateway requires `list_capabilities` and `describe_capability` on `CapabilityRuntimeService`, but those operations are absent from the frozen Wave-5 service. Adding them would change a frozen contract; using the registry directly would violate the same projection boundary. It was not merged.

### Python and agent projection — accepted and integrated

Candidate head `c62aa2bbe103f12c641d60cf818f5b2acaf8f172` remains integrated by `a530cf7d4fac4347e2dd520c14311c8ccbfad86c`. Its three focused tests pass on the integration branch. The facade and immutable internal-agent adapter use only the frozen runtime availability, application-scoped discovery, and invocation APIs; no registry, endpoint, or consumer-owned invocation logic is present.

## Directly Dependent Verification #2

- MCP focused suite: passed, 3 tests.
- REST focused loopback suite: passed, 3 tests outside the managed sandbox socket restriction.
- Python and agent focused suite: passed, 3 tests.
- `git diff --check`: passed for the integration worktree and both unmerged candidate diffs.

## Next Action #2

Return a corrected MCP candidate that delegates all discovery through the frozen runtime boundary, and a REST candidate whose routes can be served solely by the frozen runtime API. Review composition only after all three projections are integrated. Acceptance remains blocked and was not launched.

## Corrected Projection Candidate Review

`contractsStatus: frozen` remains in force. Acceptance was not launched or reviewed.

### MCP projection — accepted and integrated

Candidate `d41d327066adaa7bf0be5c137247c842b6b3f6bd` changes only its owned package, focused tests, and canonical handoff relative to the current integration base. It consumes `CapabilityConsumerFacade` for static discovery, availability, and invocation; it neither accesses `CapabilityRegistry` nor constructs `CapabilityRuntimeService`. Its focused suite passed, 3 tests, and it was merged by `1d480c5cc0e636e6e78daffd1d2457dfa27f0d6c`.

### REST projection — accepted and integrated

Candidate `a5d2b5d014e26db3a7967615ece7b5bed0953ac2` changes only its owned service, focused tests, and canonical handoff relative to the current integration base. All discovery, availability, and invocation actions delegate through the injected consumer-facade boundary; it contains no `CapabilityRegistry` access and does not construct `CapabilityRuntimeService`. Its focused loopback suite passed, 3 tests, outside the managed sandbox's socket restriction, and it was merged by `10bc05d503a9a772c3a828a9b5833fe77fbd5ae2`.

### Python and agent projection — remains integrated

The already accepted Python and agent candidate remains integrated by `a530cf7d4fac4347e2dd520c14311c8ccbfad86c`.

## Next Action #3

All three projection candidates are integrated. Compose their integration-owned wiring before launching acceptance; acceptance remains blocked and was not launched.

## Acceptance Candidate Review

Acceptance candidate `1dc64cc9fb75edd32a7b8daf9fc89a1b195cecbc` changes only the Wave-6 acceptance journey and its canonical handoff. Its one focused test passed with the required loopback-socket permission: it verifies one Research Notes result through MCP, REST, the Python client, and the agent adapter; confirms availability becomes unavailable after stop without losing static definitions; and retains the AP-01A `math.calculate` MCP tool. It was merged by `f5b99900894489bf823850c7d808b14270ca1e9b`.

The candidate emitted two subprocess-handle `ResourceWarning`s during teardown, but the referenced processes were no longer running after the test. Wave-6 is awaiting the agreed final verification gate and is not marked complete.

## Final Verification

`make verify-wave-06` passed after acceptance integration. The agreed minimal gate covered the three projection suites, the one Wave-6 acceptance journey, the direct Wave-5 invocation smoke, the existing MCP discovery smoke, dependency-lock verification, `pip check`, compilation of Wave-6 paths, and `git diff --check`.

The acceptance and Wave-5 journeys emitted teardown-time `ResourceWarning`s for already-exited subprocess handles; no referenced process remained running. Wave-6 is verified pending a separate closure decision and is not marked complete.

## Wave-6 Completion

Wave-6 is complete on `integration/phase2-wave6` only. The final verified integration head before this completion record is `5566437051e05df68446b48fcee6391e3646a8bd`; this closure does not merge the branch into `main`.

The readiness decisions use the required machine-readable `accepted` value for every lane, and the integration queue uses `WAVE COMPLETE`. The detailed review rationale remains recorded in the candidate and verification evidence below.

### Candidate and Integration Commits

- MCP candidate `d41d327066adaa7bf0be5c137247c842b6b3f6bd`; integrated by `1d480c5cc0e636e6e78daffd1d2457dfa27f0d6c`.
- REST candidate `a5d2b5d014e26db3a7967615ece7b5bed0953ac2`; integrated by `10bc05d503a9a772c3a828a9b5833fe77fbd5ae2`.
- Python and agent candidate `c62aa2bbe103f12c641d60cf818f5b2acaf8f172`; integrated by `a530cf7d4fac4347e2dd520c14311c8ccbfad86c`.
- Acceptance candidate `1dc64cc9fb75edd32a7b8daf9fc89a1b195cecbc`; integrated by `f5b99900894489bf823850c7d808b14270ca1e9b`.
- Integration-owned facade `206fd52ad1da61527bf72b4cb0a34e080d6a73df`, projection composition `a8f74d94b0d661baf10bddf87dd7c802322f5e7d`, and loopback REST CLI `10fe12b62e90c801c391f08b69d61eace628c640`.

### Completion Evidence

- `make verify-wave-06` passed at the final verified head, including the accepted Wave-6 journey and required focused smoke checks.
- `make verify-current` passed for the configured readiness milestone.
- `make agent-handoff` passed and produced `.agent/handoff.md`.
- `scripts/agents/wave_status.sh --wave wave-06` reported clean worktrees, ready prompts and handoffs, and `contractsStatus: frozen`.
- `git diff --check` and `git status --porcelain` were clean at verification time.

### Known Limitations

- REST remains literal IPv4 loopback only (`127.0.0.1`); no remote hosting, authentication, TLS, or automatic route publication is supplied.
- The acceptance and Wave-5 lifecycle tests emit teardown-time `ResourceWarning`s for already-exited subprocess handles; no process leak was observed.
- MCP remains an optional projection and the pre-existing AP-01A MCP tool behavior is preserved.

### Rollback Order

To remove Wave-6 safely, revert in reverse integration order: this completion record; acceptance merge `f5b99900894489bf823850c7d808b14270ca1e9b`; CLI `10fe12b62e90c801c391f08b69d61eace628c640`; composition `a8f74d94b0d661baf10bddf87dd7c802322f5e7d`; REST merge `10bc05d503a9a772c3a828a9b5833fe77fbd5ae2`; MCP merge `1d480c5cc0e636e6e78daffd1d2457dfa27f0d6c`; Python/agent merge `a530cf7d4fac4347e2dd520c14311c8ccbfad86c`; then facade `206fd52ad1da61527bf72b4cb0a34e080d6a73df`.
