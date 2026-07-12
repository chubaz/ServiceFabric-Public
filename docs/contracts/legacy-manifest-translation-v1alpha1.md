# Legacy Manifest Translation v1alpha1

Legacy `fabric-manifest.json` files are template advice, not canonical contracts. Translation combines exact source bytes with explicit context and an allowlisted profile. Only `APP_NAME` and `APP_SLUG` are substituted; no template engine, environment expansion, imports, path traversal, or network access occurs.

Static Vite and React templates can become experimental `managed_static` packages only with explicit identity, owner, version, immutable bundle reference and digest. Internal Compose URLs and host paths become portability diagnostics. Compilation, execution and avoidance rules remain advisory and are never converted into tools, effects, permissions or network authority.

Shared-host Flask manifests require a future adapter or migration. Python manifests require an explicit immutable process artifact. Composite UI/Python manifests require split review. Reports always require human review and never claim deployment readiness.

Use `inventory_legacy_manifests.py --check` for repository assessment and `translate_legacy_manifest.py --input ... --context ... --output ... --report ... --strict` for one explicit source. Exit codes are 0 translated, 2 context/review required, 3 invalid/unsupported/unsafe, and 4 internal safe failure.
