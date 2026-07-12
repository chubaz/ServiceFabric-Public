# ADR-0005: Repository-Native Agent Execution

Status: Accepted
Date: 2026-07-12

Stable instructions live in `AGENTS.md`; milestone instructions live in `docs/workplans`; machine execution rules are committed JSON. Repository commands own preflight and verification, allowing agent prompts to describe only deltas. Post-C1 work uses the compressed V1-V4 sequence. Commands are allowlisted arrays and never arbitrary shell strings.
