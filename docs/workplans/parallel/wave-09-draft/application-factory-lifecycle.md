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

Wave-9 will need lifecycle-owned records that reference—not replace—the canonical contracts: application identity mapping, blueprint/profile approval, candidate-review decision, escalation, and integration closure. Their storage and schema are intentionally not specified by this draft.

## Wave-8-dependent assumptions

**Wave-8-dependent assumption:** a provider request produces a reliable normalized result, events can be collected and retained, recovery is invoked when required, policy limits are enforced across concurrent attempts, and timeout/cost/cancellation behavior has an operational definition. The current contracts expose envelopes for these behaviors; they do not provide lifecycle approval or review semantics.
