# Candidate review and publication

Analysis creates candidates only. A `DistillationDecision` from a named reviewer approves, rejects, or requests revision; provider output and confidence scores never approve publication.

- Approved capabilities publish through the existing `CapabilityRegistry`.
- Approved technique policies publish through the exact-version `TechniquePolicyCatalog`.
- Approved engineering patterns publish through the engineering-distillation lane's exact-version file-backed `EngineeringPatternCatalog`.
- Blueprint and system proposals remain proposals only.

Publication is deterministic and idempotent. It does not modify ServiceFabric core source, blueprints, application source, or factory records. Conflicting exact versions fail atomically rather than overwrite existing definitions.
