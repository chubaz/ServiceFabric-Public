# ServiceFabric Specification Map

Last updated: 2026-07-11
Repository baseline: `b1245e4fc38b0c6ea222ea62986f479dd1fd2eef`
Authority order source: `../ServiceFabric Formal Refactoring Plan for Codex.md`

This index records the canonical ServiceFabric design inputs discovered from the parent `Tool Builder` folder. The source documents remain external to this repository and are referenced here by relative path and SHA-256 digest.

| Spec ID | Canonical document title | Relative path | SHA-256 | Relevant sections for current work | Governing PRs |
| --- | --- | --- | --- | --- | --- |
| `SF-SPEC-001` | Canonical ServiceFabric Tool Manifest v1 | `../Canonical ServiceFabric Tool Manifest v1.md` | `4af5d93b43aee8e519eccff09de03d0e15a9eb1e246987c79e6b95f3800efe67` | `1. Purpose`, `2. Core design rules` | `P0-00`, future contract PRs |
| `SF-SPEC-002` | ServiceFabric Tool Capsule Runtime Framework v1 | `../ServiceFabric Tool Capsule Runtime Framework v1.md` | `7f502b99cfbc1f82d26a2309afc69f15bcf5e9aec44fadf0b6db3d2906769115` | `1. Purpose` | `P0-00`, future runtime PRs |
| `SF-SPEC-003` | Building Graph Specification v1 | `../Building Graph Specification v1.md` | `6a75d960b9853a97dbb53d29cf1dc916c669ff63b3f4985525438487d899cb9b` | `1. Purpose` | `P0-00`, future build-graph PRs |
| `SF-SPEC-004` | ServiceFabric System-Maintenance Graph Specification v1 | `../ServiceFabric System-Maintenance Graph Specifica.md` | `08add4629777bc36edaab0edb904f60d5d4062e510dfbba4b75f6d4ff0fc466a` | `1. Purpose` | `P0-00`, future maintenance PRs |
| `SF-SPEC-005` | ServiceFabric System-Evolution Graph Specification v1 | `../ServiceFabric System-Evolution Graph Specificati.md` | `5091741812b0a0d9361e9b052b53f4654403743cd930588fdf4c1b2d7ffe7243` | `1. Purpose` | `P0-00`, future evolution PRs |
| `SF-SPEC-006` | ServiceFabric Tool Registry, Capability Discovery, and Routing Specification v1 | `../ServiceFabric Tool Registry  Capability Discover.md` | `711b798b3788b32e2daedac492dd55d5045742d002c6e6adea98edacee637526` | `1. Purpose` | `P0-00`, future registry PRs |
| `SF-SPEC-007` | ServiceFabric Security, Identity, Authorization, Approval, and Side-Effect Governance Framework v1 | `../ServiceFabric Security  Identity  Authorization.md` | `7aedbf3de6e521666b4552b78489c82b9facbac92b03d288495f9caba8f12819` | `1. Purpose`, primary policy rule | `P0-00`, `P0-01`, future security PRs |
| `SF-SPEC-008` | ServiceFabric Telemetry, Evaluation, and Agent-Callability Testing Framework v1 | `../ServiceFabric Telemetry  Evaluation  and Agent-C.md` | `57b5dcebc8ac22d53522cda8c9a79e97124f5a19deccc4f62778b083a20b1e4e` | `1. Purpose` | `P0-00`, future evaluation PRs |
| `SF-SPEC-009` | ServiceFabric Domain Tool Portfolio and Prioritisation Framework v1 | `../ServiceFabric Domain Tool Portfolio and Prioriti.md` | `fa16195442fb5502bfebff6c0bc4f9ef9caba6a492d2b5534b48fd9b601f708c` | `1. Purpose` | `P0-00`, future portfolio PRs |
| `SF-SPEC-010` | ServiceFabric Stage 11 Reference Implementations | `../servicefabric-stage11/README.md` | `f74342810483a96c9d54208cb2f889df37ddfd8a3ffc6dd86727f6de11f97b42` | overview of reference implementation scope | `P0-00`, future stage-12 migration PRs |
| `SF-SPEC-011` | ServiceFabric Production Architecture, Roadmap, and Engineering Standards v1 | `../ServiceFabric Production Architecture  Roadmap.md` | `1a879d5fafad028734d046467e8ed3c496e890f44904d7223824b821ab3e1208` | `1. Executive architectural decisions` | `P0-00`, future productionization PRs |

## Notes

- `SF-SPEC-003` was located from the parent folder by the document heading `Building Graph Specification v1`.
- `SF-SPEC-010` was located from the parent folder by the document heading `ServiceFabric Stage 11 Reference Implementations` in `../servicefabric-stage11/README.md`.
- Future pull requests should cite the relevant `SF-SPEC-*` identifiers and any applicable ADR identifiers together.
