# Wave-8 Integration Handoff

`contractsStatus: frozen` remained in force. Wave-8 completion was recorded on `integration/phase25-wave8` only, and this closure does not merge to `main`.

## Completion Summary

- All seven specialist lanes were accepted and integrated.
- The final verified head was `1a898c35b2dc72f8ee42a1fc92a75fd8f676b428`.
- Completion support commit: `fix(cli): make provider doctor import-light`.
- The Wave-8 completion metadata was then written from that verified state.

## Candidate Review and Integration Commits

| Lane | Candidate commit(s) | Decision | Integration commit |
| --- | --- | --- | --- |
| provider-runtime | `bef2e1666fdd7bf93a8bc6bfe274d77d91c1dc3f` | accepted | `3facb3f` |
| pi | `b7162d61e0fd7660f63b2eb1a0821e6df3ee1259` | accepted | `65fac53` |
| codex | `b7b40e670451413944639afb4362930aef28b7a2` | accepted | `0e26c86` |
| claude | `e9aaeabaa12761fb487fb7c242b34c463a4b1417` | accepted | `18321b7` |
| gemini | `3dadd52` then `a5d2528db810693155a953bf582b0339ffc571ac` | accepted after provider ID correction | `a1a4b32` |
| langgraph | `f007c34815719c38f10d88bdfc4b414d8e5ac839` | accepted replacement | `739a568` |
| evaluation | `efec8425a051010eb9e850b9c53d7f46a8131499` | accepted | `a933a4f` |

All specialist lanes are integrated. The integration queue and readiness metadata now record completion.

## Exact Verification Evidence

- `servicefabric agents providers doctor` passed and returned structured diagnostics for all four providers.
- `make verify-wave-08` passed. The gate covered:
  - `integration/phase25-wave8/verify_boundaries.py`
  - `tests/agent_provider_contracts`
  - `tests/agent_provider_runtime`
  - `tests/langgraph_orchestration`
  - `tests/pi_harness`
  - `tests/codex_adapter`
  - `tests/claude_code_adapter`
  - `tests/gemini_cli_adapter`
  - `tests/wave_08`
  - `tests.wave_07.test_framework_journey`
  - `scripts/dependencies/check_python_locks.py`
  - `compileall` for the Wave-8 provider and integration paths
  - `git diff --check`
- `python3 scripts/agent/wave_completion.py --wave wave-08 --format json` passed after the completion markers were written.

## Adapter Conformance Results

- `provider-runtime`: owns subprocess execution, cancellation, timeout handling, and runtime event emission.
- `pi`: only builds argv and parses provider output; no subprocess ownership.
- `codex`: only builds argv and parses provider output; no subprocess ownership.
- `claude`: only builds argv and parses provider output; no subprocess ownership.
- `gemini`: only builds argv and parses provider output; no subprocess ownership.
- `langgraph`: delegates readiness to `ready_tasks`, consumes the Wave-7 task pack, and does not derive local task state or render prompts itself.
- `evaluation`: black-box only; no provider call occurs in automated tests.

## Optional Provider Doctor Result

`servicefabric agents providers doctor` succeeded, but each provider was reported unavailable in the active lane venv because the adapter distributions were not installed there:

- `claude`: `servicefabric_claude_code_adapter` missing
- `codex`: `servicefabric_codex_adapter` missing
- `gemini`: `servicefabric_gemini_cli_adapter` missing
- `pi`: `servicefabric_pi_harness` missing

That result is environment-specific and separate from the formal Wave-8 verification gates.

## Completion Support

The only support change made during finalization was the CLI import fix that keeps provider inspection import-light in the current lane environment. It does not change the specialist-owned execution contracts.

## Known Limitations

- Wave-8 remains on `integration/phase25-wave8`; it is not merged into `main`.
- Provider doctor depends on the active lane venv having the adapter distributions installed.
- No credentials or full environment snapshots are persisted.
- Provider calls remain excluded from automated tests.
- Path ownership remains disjoint across provider-specific packages and lane-owned integration code.

## Rollback Order

1. Revert this completion record commit.
2. Revert the completion support commit `1a898c35b2dc72f8ee42a1fc92a75fd8f676b428`.
3. Revert the integration commits in reverse dependency order: evaluation `a933a4f`, langgraph `739a568`, gemini `a1a4b32`, claude `18321b7`, codex `0e26c86`, pi `65fac53`, provider-runtime `3facb3f`.
4. Leave the frozen Wave-7 contracts and specialist-owned candidate branches untouched unless a separate rollback is explicitly required.
