# Application-factory lifecycle

| Stage | Entry | Authority | Success / blocked exit | Escalate when |
|---|---|---|---|---|
| Intent to application | Accepted `ApplicationIntent` | Factory authority | Bind or validate application identity; block unresolved modify/debug target | identity, scope, or product decision is ambiguous |
| Blueprint generation | Identified intent | Blueprint compiler | Produce bounded `AgentRunPlan`; block unsafe or underspecified decomposition | constraints or capability mapping conflict |
| Profile and blueprint approval | Candidate plan/profile | Named approver | Approve, reject, or request revision | risk, cost, path, or resource decision exceeds policy |
| Candidate execution | Approved, dependency-ready task | Provider runtime | Produce normalized execution result; block non-success or absent usable task result | provider policy, timeout, cost, or runtime recovery needs a disposition |
| Candidate review | Task result and evidence | Candidate reviewer | Accept, reject, rework, or escalate | changed-path conflict, weak evidence, failed verification, unresolved blocker |
| Application integration and closure | Required accepted candidates | Application integration authority | Return `AgentHandoff`; success means approved integrated application with no unresolved blockers | conflict, missing dependency, or closure decision cannot be resolved |
| Requirement escalation | Any authority boundary | Product/application owner | Decision permits revision, retry, or closure | no authorized decision exists |

Factory lifecycle state owns only approvals, candidate-review decisions, unmet requirements, and final-handoff references. It references Wave-7 run IDs and results through `FileRunStore`; it does not copy task, provider, event, usage, or generic run state.

Provider execution is supplied by the completed Wave-8 runtime. Factory approval remains mandatory before repository bootstrap or candidate execution, and a candidate result remains evidence until an explicit review decision is recorded.
