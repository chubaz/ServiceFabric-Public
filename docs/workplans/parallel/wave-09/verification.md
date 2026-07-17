# Verification and evaluation

`make verify-wave-09` runs the factory-contract suite, the six implementation-package suites, one Wave-9 journey, one Wave-8 provider-execution smoke, one application-generator/blueprint smoke, lock validation, `pip check`, compileall for Wave-9 paths, and `git diff --check`. It must not invoke prior Wave verification targets.

The contract-first black-box journey uses only local fakes and fixtures. It demonstrates approval, isolated candidate execution, review, accepted-commit integration, verification evidence, handoff, and unmet-requirement reporting without real provider calls.
