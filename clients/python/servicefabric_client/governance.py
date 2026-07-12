"""Typed client delegation for internal governance operations."""
class GovernanceClient:
 def __init__(self,service):self._service=service
 def evaluate_policy(self,request,**kwargs):return self._service.evaluate_policy(request,**kwargs)
 def submit_operation(self,operation,initial_event,**kwargs):return self._service.submit_operation(operation,initial_event,**kwargs)
 def get_operation(self,operation_ref):return self._service.get_operation(operation_ref)
 def list_operation_events(self,operation_ref):return self._service.list_operation_events(operation_ref)
 def create_approval_request(self,*args,**kwargs):return self._service.create_approval_request(*args,**kwargs)
 def record_approval_decision(self,*args,**kwargs):return self._service.record_approval_decision(*args,**kwargs)
 def create_approval_binding(self,*args,**kwargs):return self._service.create_approval_binding(*args,**kwargs)
 def request_cancellation(self,operation_ref,**kwargs):return self._service.request_cancellation(operation_ref,**kwargs)
 def transition(self,operation_ref,to_state,**kwargs):return self._service.transition(operation_ref,to_state,**kwargs)
 def reconcile(self,**kwargs):return self._service.reconcile(**kwargs)
 def effect_receipts(self,operation_ref):return self._service.effect_receipts(operation_ref)
