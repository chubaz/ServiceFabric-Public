# Wave-4 Integration Handoff

## Completion decision

Wave-4 is closed by integration authority on `integration/phase2-wave4`. All four specialist lanes are integrated, contracts remain frozen, and `integration-queue.json` is `WAVE COMPLETE`. This closes Wave-4 only; no merge into `main` was performed.

Final integration HEAD before this closure record: `90e37e47b4b51f45e1b50de3082bdcdbee6460b6` (`fix(agents): provision Wave-4 model and registry packages`).

## Specialist candidates and integration commits

- `operation-model`: candidate series `0c21e47596d1f87255613987c18ecb0ca98827b7`, `495b2b98df66124e60ff1dbb335ebc3aaa6f97d3`, and accepted head `3c0f867f444776efc21700722561482e90ecf1d0`; integrated by `ba161c89ecb9f888e00071b89c30f213ef53f2f4`.
- `capability-model`: accepted candidate `786d23fe197ec7c3fd407448334962ca11f44340`; integrated by `99a3c721133485e2e1f9ba5b7da295ed50257de6`.
- `capability-registry`: returned initial candidate `4eaab5af167781b97260aaf6e74099523e73d374`; correction series `df27a6625bf09f3d76e8d0c91d0265d63ac0761d`, `3866227a9b3f4363654e86790391e76af83e5686`, and `94d34c4402fe81ff2edb9c78c12cc2b17b726b69`; accepted head `cb5a6f853a48aab403d4d228325bdc64398b6a6d`; first correction integration `1d5a705e40c544eafc643ee314317456edddb49f`; final integration `7aa4f25ede41fc1112ee8f9c2cbdffa577084fde`.
- `capability-authoring`: returned initial candidate `2e3d9d06e1b0c3fd66bd72726cf05fe068df4406`; correction series `991507d97474abc05ac43ef578bbe1a1f49d8d70`, `32df8961939f606dc632ba2f161f73e1c42f2bce`, and `d762ca1168841289b79d6e72aab136d5639dc331`; accepted head `2a67901d3e60204313d3f54401ef82903295c92b`; first correction integration `8022f87c6f9fa088b67fc6c80fd11e71af5c4930`; final integration `5fc13ada75b8eab12523482614b0b024f214f3c6`.
- Integration composition: `be7c0a0be48c211b4a13b64e76d1d84f769e7a71`; runtime provisioning: `90e37e47b4b51f45e1b50de3082bdcdbee6460b6`.

## Registered Research Notes capabilities

- `create-note` → `notes.create`, database-write effect.
- `get-note` → `notes.get`, database-read effect.
- `search-notes` → `notes.search`, database-read effect.

Each capability is a static definition with one exact operation reference. Registration, list, and describe are deterministic static-registry actions; no invocation, availability, MCP, REST, Python, or `ToolDefinition` projection is introduced.

## Verification record

Executed after `source .agent-runtime.env`:

- `python3 -m unittest discover -s tests/agent -v` — passed (41 tests) after the temporary fresh runtime was permitted to resolve its locked dependencies.
- `make verify-wave-04` — waived. Wave-1 completed, including 28 AP-01A tests; Wave-2 failed in `ResearchNotesRuntimeJourneyTests.test_cli_delegates_the_required_development_commands` with `ApplicationNotFound: application 'research-notes' is not registered`. This is an inherited Wave-2 runtime/workspace regression, not a Wave-4 specialist failure.
- `make verify-current` — passed before closure.
- `git diff --check` — passed before closure.

## Known limitations and follow-up

The full cross-wave gate is not green because of the waived inherited Wave-2 Research Notes runtime regression above. `python3 scripts/agent/wave_completion.py --wave wave-04` also remains blocked because its modern duplicate manifest (`config/agents/wave-04/wave.yaml`) omits the committed readiness and queue paths, so it looks for nonexistent files under `config/agents/wave-04/`; the authoritative Wave-4 records updated by this closure are under `config/agent/waves/wave-04/`. The fresh-runtime agent test requires package resolution when its cache is empty. Capability persistence remains local JSON with POSIX `fcntl` locking, and Wave-4 intentionally provides no runtime availability or consumer projection.

## Rollback order

1. Revert this closure commit to restore the pending queue and readiness state.
2. Revert `90e37e47b4b51f45e1b50de3082bdcdbee6460b6` if the Wave-4 runtime provisioning change must be removed.
3. Revert integration composition `be7c0a0be48c211b4a13b64e76d1d84f769e7a71`.
4. Revert the final integration merges in reverse dependency order: `7aa4f25ede41fc1112ee8f9c2cbdffa577084fde`, `5fc13ada75b8eab12523482614b0b024f214f3c6`, `99a3c721133485e2e1f9ba5b7da295ed50257de6`, then `ba161c89ecb9f888e00071b89c30f213ef53f2f4`.

No merge into `main` is part of this rollback or completion decision.
