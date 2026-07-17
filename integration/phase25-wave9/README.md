# Wave-9 integration bootstrap

This directory owns the shared factory contracts, final composition, CLI wiring, dependency-lock installation, Wave-9 verification gate, and closure. Specialist implementations remain on their dedicated branches until reviewed candidate integration.

The factory consumes completed Wave-8 provider execution through its canonical runtime. It must not create a second provider runtime, task scheduler, application generator, framework-kit catalogue, capability registry, or generic run store.
