import unittest
from datetime import datetime,timezone
from servicefabric_contracts.operations import ServiceFabricOperation
from servicefabric_mcp_projection import project_task
NOW=datetime(2030,1,1,tzinfo=timezone.utc)
def operation():return ServiceFabricOperation.model_validate({"apiVersion":"servicefabric.ai/v1alpha1","kind":"ServiceFabricOperation","metadata":{"id":"operation-1","name":"Operation","description":"Fixture.","owner_ref":{"kind":"service","id":"controller"}},"spec":{"operation_id":"operation-1","request_ref":"request-1","invocation_ref":"invocation-1","tool_id":"math.calculate","revision_ref":"1.0.0","state":"running","progress":50,"created_at":NOW,"updated_at":NOW,"cancellation":{"cancellable":True,"cancellation_state":"not_requested"}}})
class DurableProjectionTests(unittest.TestCase):
 def test_task_view_is_non_authoritative_projection(self):
  task=project_task(operation(),client_supports_tasks=True);self.assertEqual((task.task_id,task.operation_ref,task.progress),("operation-1","operation-1",50));self.assertIsNone(project_task(operation(),client_supports_tasks=False))
if __name__=="__main__":unittest.main()
