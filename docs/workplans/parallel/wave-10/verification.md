# Verification

`make verify-wave-10` is focused: shared contracts, six implementation package suites, one Wave-10 journey, one Wave-9 factory smoke, one Wave-4 capability-registry smoke, one release-doctor smoke, dependency-lock validation, isolated `pip check`, compileall for Wave-10 paths, and `git diff --check`.

The target must not recursively invoke Waves 1–9. During bootstrap, package and journey suites may be absent; the boundary verifier confirms the declared final gate without pretending specialist work exists. Closure runs the complete target, followed by one `make verify-current`.
