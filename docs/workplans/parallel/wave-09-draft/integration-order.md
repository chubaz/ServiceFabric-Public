# Draft integration order

1. Integration freezes this draft’s scope and records the Wave-8 closure gate.
2. Technology-profile and blueprint-compiler lanes independently refine selection and task-DAG rules.
3. Factory-bootstrap consumes those proposals to refine lifecycle, approval, and escalation boundaries.
4. Application-integration defines candidate acceptance and application closure using the resulting lifecycle.
5. Evaluation applies the design to the Research Workspace OS exemplar, including failure and recovery measures.
6. Integration accepts, returns, or rejects draft changes and publishes one coherent planning set.

No parallel lane may implement a factory component. A future implementation order must begin only after explicit Wave-8 closure and a separately approved Wave-9 implementation workplan.

## Wave-8-dependent assumptions

**Wave-8-dependent assumption:** any future step that dispatches candidate work, interprets provider events/results, applies cost or concurrency limits, or reconciles timeout/cancellation depends on completed Wave-8 runtime behavior. Those steps are deliberately absent from this draft integration order.
