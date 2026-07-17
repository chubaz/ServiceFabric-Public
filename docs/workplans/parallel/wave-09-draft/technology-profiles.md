# Technology profiles

## Decision before development

Before any candidate task is released, a technology-profile decision selects an exact reviewed framework-kit version for each proposed module. It records the kit ID/version, primitive, adapter ID, runtime family, supported lifecycle states, bounded technique-policy references, open resource-compatibility questions, and provider-policy references. It is governance data and planning input, never executable provider configuration.

| Reviewed kit | Primitive | Runtime family | Development / build / runtime |
|---|---|---|---|
| `fastapi-service@1.0.0` | service | python | yes / yes / yes |
| `react-web@1.0.0` | web | node | yes / yes / yes |
| `python-library@1.0.0` | library | python | no / yes / no |

The selection accepts only primitive-compatible reviewed kits with the lifecycle support demanded by the intent. A missing kit, primitive mismatch, unsupported lifecycle, conflicting runtime constraint, unmapped capability, or unresolved resource question is rejected or escalated. A `python-library` profile cannot be approved for factory-driven development or a runnable runtime target from the catalog metadata alone.

`ApplicationIntent.constraints` and `requested_capabilities` are declarative selection inputs. They must not become provider arguments, environment values, model settings, credentials, or arbitrary request metadata.

## Wave-8-dependent assumptions

**Wave-8-dependent assumption:** provider eligibility and execution limits can be referenced through a completed and enforced `ProviderPolicy`. A profile must not infer that a reviewed kit authorizes provider invocation, resource provisioning, or a process runtime. Secret-free metadata and name-only environment entries remain mandatory at the provider boundary.
