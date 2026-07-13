import unittest
from dataclasses import replace
from datetime import datetime,timedelta,timezone
from servicefabric_contracts import ApprovalBinding,ToolInvocationAcceptance,ToolInvocationRequest,ToolResult
from servicefabric_contracts.approvals import ApprovalBindingSpec,ApprovalScope
from servicefabric_contracts.budgets import ExecutionBudget
from servicefabric_contracts.effects import EffectDeclaration
from servicefabric_contracts.governance import AuthorityGrant
from servicefabric_contracts.metadata import OwnerReference,ResourceMetadata
from servicefabric_contracts.permissions import PermissionRequirement
from servicefabric_governance import ApprovalService,GovernedInvocationBoundary,InvocationGovernanceProfile,PolicyBundle,VersionedPolicyEvaluator
from servicefabric_governance.invocation_boundary import _digest
NOW=datetime(2030,1,1,tzinfo=timezone.utc);D="sha256:"+"a"*64
class Runtime:
 def __init__(self):self.calls=[]
 def invoke(self,request):
  self.calls.append(request);return ToolResult(apiVersion="servicefabric.ai/v1alpha1",kind="ToolResult",status="success",invocation_id=request.spec.request_id,tool_id=request.spec.target.tool_id,revision_ref=request.spec.target.revision_ref,started_at=NOW,completed_at=NOW,duration=timedelta(),data={"ok":True})
def request(arguments={"value":1},approval_refs=()):return ToolInvocationRequest.model_validate({"apiVersion":"servicefabric.ai/v1alpha1","kind":"ToolInvocationRequest","metadata":{"id":"request-1","name":"Request","description":"Fixture.","owner_ref":{"kind":"service","id":"test"}},"spec":{"request_id":"request-1","target":{"target_kind":"revision","tool_id":"math.calculate","revision_ref":"1.0.0"},"arguments":arguments,"caller_context":{"subject_ref":"user-alice","principal_type":"human","tenant_ref":"tenant-demo","issuer":"identity","scopes":["math-calculate"],"authentication_strength":"multi_factor"},"protocol_context":{"protocol":"mcp","adapter_ref":"trusted-mcp-adapter"},"budget":{},"approval_refs":approval_refs}})
def profile(effect="none"):
 return InvocationGovernanceProfile("math.calculate","1.0.0",(EffectDeclaration(effect_type=effect,target_category="task",scope="fixture",reversibility="not_applicable" if effect=="none" else "reversible",verification_required=False,approval_required=effect!="none",idempotency_required=False),),(PermissionRequirement(permission_id="math-calculate",tenant_scope="caller_tenant",resource_scope="fixture"),),AuthorityGrant(scopes=("math-calculate",),tenant_ref="tenant-demo"),ExecutionBudget(),"low","policy-demo","1.0.0",D)
def boundary(bundle,profile_value,binding=None):
 runtime=Runtime();value=GovernedInvocationBoundary(evaluator=VersionedPolicyEvaluator((bundle,)),approvals=ApprovalService(),runtime=runtime,profiles=(profile_value,),approval_lookup=lambda _ref:binding);return value,runtime
def bundle(*,denied=(),approval=()):return PolicyBundle(bundle_id="policy-demo",version="1.0.0",digest=D,allowed_scopes=("math-calculate",),denied_effects=denied,approval_effects=approval)
class GovernanceIntegrationTests(unittest.TestCase):
 def test_allowed_policy_executes_only_after_evaluation(self):
  value,runtime=boundary(bundle(),profile());self.assertEqual(value.invoke(request(),trusted_adapter_ref="trusted-mcp-adapter",now=NOW).status,"success");self.assertEqual(len(runtime.calls),1)
 def test_denied_and_approval_required_calls_do_not_execute(self):
  value,runtime=boundary(bundle(denied=("none",)),profile());self.assertEqual(value.invoke(request(),trusted_adapter_ref="trusted-mcp-adapter",now=NOW).error.code,"SF-AUTHZ-DENIED");self.assertEqual(runtime.calls,[])
  value,runtime=boundary(bundle(approval=("task_create",)),profile("task_create"));self.assertEqual(value.invoke(request(),trusted_adapter_ref="trusted-mcp-adapter",now=NOW).error.code,"SF-APPROVAL-REQUIRED");self.assertEqual(runtime.calls,[])
 def test_approval_binding_requires_exact_unexpired_intent(self):
  intent=_digest({"tool":"math.calculate","revision":"1.0.0","caller":"user-alice","arguments":{"value":1}});argument=_digest({"value":1})
  binding=ApprovalBinding(apiVersion="servicefabric.ai/v1alpha1",kind="ApprovalBinding",metadata=ResourceMetadata(id="binding-1",name="Binding",description="Fixture.",owner_ref=OwnerReference(kind="service",id="approval")),spec=ApprovalBindingSpec(binding_id="binding-1",approval_request_ref="request-a",approval_decision_ref="decision-a",approval_decision_digest=D,policy_decision_ref="policy-a",policy_version="1.0.0",caller_ref="user-alice",operation_ref="operation-1",tool_id="math.calculate",revision_ref="1.0.0",intent_digest=intent,argument_digest=argument,effect_class="task-create",authority_scope=ApprovalScope(effect_refs=("task-create",),authority=AuthorityGrant(scopes=("math-calculate",))),valid_from=NOW-timedelta(minutes=1),valid_until=NOW+timedelta(minutes=1),binding_digest=D))
  value,runtime=boundary(bundle(approval=("task_create",)),profile("task_create"),binding);self.assertEqual(value.invoke(request(approval_refs=("binding-1",)),trusted_adapter_ref="trusted-mcp-adapter",now=NOW).status,"success");self.assertEqual(len(runtime.calls),1)
  value,runtime=boundary(bundle(approval=("task_create",)),profile("task_create"),binding);self.assertEqual(value.invoke(request(arguments={"value":2},approval_refs=("binding-1",)),trusted_adapter_ref="trusted-mcp-adapter",now=NOW).error.code,"SF-APPROVAL-INVALID");self.assertEqual(runtime.calls,[])
  expired=binding.model_copy(update={"spec":binding.spec.model_copy(update={"valid_until":NOW})});value,runtime=boundary(bundle(approval=("task_create",)),profile("task_create"),expired);self.assertEqual(value.invoke(request(approval_refs=("binding-1",)),trusted_adapter_ref="trusted-mcp-adapter",now=NOW).error.code,"SF-APPROVAL-INVALID");self.assertEqual(runtime.calls,[])
  approvals=ApprovalService();runtime=Runtime();value=GovernedInvocationBoundary(evaluator=VersionedPolicyEvaluator((bundle(approval=("task_create",)),)),approvals=approvals,runtime=runtime,profiles=(profile("task_create"),),approval_lookup=lambda _ref:binding);self.assertEqual(value.invoke(request(approval_refs=("binding-1",)),trusted_adapter_ref="trusted-mcp-adapter",now=NOW).status,"success");self.assertEqual(value.invoke(request(approval_refs=("binding-1",)),trusted_adapter_ref="trusted-mcp-adapter",now=NOW).error.code,"SF-APPROVAL-INVALID")
 def test_constrained_allow_and_durable_acceptance_use_canonical_boundaries(self):
  constrained=replace(profile(),requested_budget=ExecutionBudget(maximum_wall_clock_ms=100))
  limited=PolicyBundle(bundle_id="policy-demo",version="1.0.0",digest=D,allowed_scopes=("math-calculate",),maximum_wall_clock_ms=10)
  value,runtime=boundary(limited,constrained);self.assertEqual(value.invoke(request(),trusted_adapter_ref="trusted-mcp-adapter",now=NOW).status,"success");self.assertEqual(len(runtime.calls),1)
  acceptance=ToolInvocationAcceptance(apiVersion="servicefabric.ai/v1alpha1",kind="ToolInvocationAcceptance",request_id="request-1",invocation_id="invocation-1",operation_ref="operation-1",accepted_at=NOW,status="accepted")
  durable=replace(profile(),durable=True);runtime=Runtime();value=GovernedInvocationBoundary(evaluator=VersionedPolicyEvaluator((bundle(),)),approvals=ApprovalService(),runtime=runtime,profiles=(durable,),durable_acceptor=lambda req,intent,now:acceptance);self.assertEqual(value.invoke(request(),trusted_adapter_ref="trusted-mcp-adapter",now=NOW).operation_ref,"operation-1");self.assertEqual(runtime.calls,[])
