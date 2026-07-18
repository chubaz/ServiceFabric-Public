# Foundation capabilities and maturity

The foundation release provides the following current capability surface.

| Capability | Foundation status | Boundary |
| --- | --- | --- |
| Canonical contracts | Available | Invocation, result, package, tool, evidence, effect, and operation records remain the authoritative integration surface. |
| Canonical runtime and operations | Available | New execution paths use the runtime; legacy dynamic execution remains contained. |
| Capability authoring, registry, and runtime | Available | Capabilities are modeled and governed through the authoritative catalog and registry. |
| Application models, assembly, and builders | Available | Applications are composed through canonical models and builder workflows. |
| Factory, blueprints, and technology profiles | Available | Creation workflows are governed records and reviewed engineering inputs. |
| Agentic and provider integrations | Available | Adapters consume canonical services and do not own tool business logic. |
| Distillation | Review-gated | Evidence produces candidates; only explicit approval may publish to authoritative catalogs. |
| Release doctor | Available | Checks local Python and package metadata only. |

## Maturity statement

This is a foundation release, suitable for repository-local engineering, deterministic evidence review, and integration against the documented canonical packages. It is intentionally not a claim of a turnkey hosted platform. Deployments, operational policy, identity, observability, provider availability, and production support depend on the adopting environment and remain outside the doctor’s scope.

The release does not auto-discover or trust remote MCP inventory, expose secret values, install dependencies, provision infrastructure, or publish distillation output without human approval. Blueprint and system proposals are records, not executable patches.

Use the [five-minute demonstration](../getting-started/foundation-release.md) to validate the local foundation surface.
