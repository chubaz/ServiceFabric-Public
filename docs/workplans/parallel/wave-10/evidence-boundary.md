# Manifest-bounded evidence

Evidence collection may read only the named Wave-9 factory record and handoff, `AgentRunPlan` tasks and task results, exact changed paths reported by those results, explicit application manifests, declared operations and capabilities, blueprint-declared source paths, and explicit documentation or verification-evidence references.

The collector must reject or ignore undeclared paths. It must not recursively scan the repository, discover arbitrary routes, infer unreported changes, or copy provider/runtime state into a new store. Bundle ordering, references, and content digests must be deterministic.
